# from neo4j import GraphDatabase
# #from typing import List
# from typing import Optional, Dict, Any, List
# from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# def get_session():
#     return driver.session()

# CREATE_FTS = "CREATE FULLTEXT INDEX chunk_text_fts IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text]"
# CREATE_VEC = "CREATE VECTOR INDEX chunk_vec_idx IF NOT EXISTS FOR (c:Chunk) ON (c.embedding) OPTIONS { indexConfig: {`vector.dimensions`: $dim, `vector.similarity_function`: 'cosine'}}"

# def ensure_indexes(dim: int):
#     with get_session() as s:
#         s.run(CREATE_FTS)
#         s.run(CREATE_VEC, dim=dim)

# UPSERT_CHUNK = """

# MERGE (cs:CaseStudy {case_id: $case_id})
# ON CREATE SET cs.title=$title, cs.url=$url
# MERGE (ch:Chunk {chunk_id: $chunk_id})
# SET ch.text=$text, ch.order=$order, ch.char_start=$start, ch.char_end=$end, ch.embedding=$embedding
# MERGE (cs)-[:HAS_CHUNK]->(ch)
# RETURN ch
# """

# def upsert_chunk(rec: dict):
#     with get_session() as s:
#         s.run(UPSERT_CHUNK, **rec)

# FIND_FTS = """

# CALL db.index.fulltext.queryNodes('chunk_text_fts', $q) YIELD node, score
# RETURN node AS chunk, score
# LIMIT $k
# """

# FIND_VEC = """

# CALL db.index.vector.queryNodes('chunk_vec_idx', $k, $qvec)
# YIELD node, score
# RETURN node AS chunk, score
# """

# def fulltext(q: str, k: int):
#     with get_session() as s:
#         return s.run(FIND_FTS, q=q, k=k).data()

# def vector(qvec: List[float], k: int):
#     with get_session() as s:
#         return s.run(FIND_VEC, qvec=qvec, k=k).data()

# GET_CONTEXT = """

# MATCH (cs:CaseStudy)-[:HAS_CHUNK]->(c:Chunk {chunk_id:$chunk_id})
# RETURN cs.case_id AS case_id, cs.title AS title, cs.url AS url,
#        c.chunk_id AS chunk_id, c.text AS text, c.order AS ord,
#        c.char_start AS s, c.char_end AS e
# """

# def get_context(chunk_id: str):
#     with get_session() as s:
#         return s.run(GET_CONTEXT, chunk_id=chunk_id).single()

# _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# def fetch_case_study(case_id: str) -> Optional[Dict[str, Any]]:
#     """
#     Returns {id, title, full_text, meta} for a CaseStudy.
#     If CaseStudy has property `full_text`, use it; otherwise join chunk texts
#     ordered by `chunk_index` (or `index` fallback).
#     """
#     with _driver.session() as s:
#         rows = s.run(
#             """
#             MATCH (c:CaseStudy {id: $id})
#             OPTIONAL MATCH (c)-[:HAS_CHUNK]->(ch:Chunk)
#             RETURN c AS cs,
#                    collect({i: coalesce(ch.chunk_index, ch.index, 0), t: ch.text}) AS chunks
#             """,
#             id=case_id,
#         ).data()
#     if not rows:
#         return None

#     cs = rows[0]["cs"]
#     chunks: List[Dict[str, Any]] = rows[0]["chunks"] or []

#     title = cs.get("title") or cs.get("name") or f"CaseStudy {case_id}"
#     # Use stored full_text if present; else assemble from chunks
#     full_text = cs.get("full_text")
#     if not full_text:
#         full_text = "\n".join(t["t"] for t in sorted(chunks, key=lambda x: x["i"]) if t.get("t"))

#     return {
#         "id": case_id,
#         "title": title,
#         "full_text": full_text or "",
#         "meta": {k: v for k, v in dict(cs).items() if k not in {"full_text"}},
#     }


# rag/store.py
from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# --- Driver & Session helpers -------------------------------------------------

_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_session():
    return _driver.session()

# --- Index creation -----------------------------------------------------------

CREATE_FTS = """
CREATE FULLTEXT INDEX chunk_text_fts IF NOT EXISTS
FOR (c:Chunk) ON EACH [c.text]
"""

CREATE_VEC = """
CREATE VECTOR INDEX chunk_vec_idx IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS { indexConfig: {`vector.dimensions`: $dim, `vector.similarity_function`: 'cosine'} }
"""

# Helpful property indexes (fast lookups by common IDs)
CREATE_CS_ID_IDX       = "CREATE INDEX cs_id_idx IF NOT EXISTS FOR (c:CaseStudy) ON (c.id)"
CREATE_CS_CASE_ID_IDX  = "CREATE INDEX cs_case_id_idx IF NOT EXISTS FOR (c:CaseStudy) ON (c.case_id)"
CREATE_CS_UUID_IDX     = "CREATE INDEX cs_uuid_idx IF NOT EXISTS FOR (c:CaseStudy) ON (c.uuid)"
CREATE_CS_SLUG_IDX     = "CREATE INDEX cs_slug_idx IF NOT EXISTS FOR (c:CaseStudy) ON (c.slug)"
CREATE_CHUNK_ID_IDX    = "CREATE INDEX chunk_id_idx IF NOT EXISTS FOR (ch:Chunk) ON (ch.id)"
CREATE_CHUNK_CID_IDX   = "CREATE INDEX chunk_chunk_id_idx IF NOT EXISTS FOR (ch:Chunk) ON (ch.chunk_id)"

def ensure_indexes(dim: int):
    """
    Creates required full-text/vector indexes and a few helpful property indexes.
    """
    with get_session() as s:
        s.run(CREATE_FTS)
        s.run(CREATE_VEC, dim=dim)

        # Property indexes (safe to re-run thanks to IF NOT EXISTS)
        s.run(CREATE_CS_ID_IDX)
        s.run(CREATE_CS_CASE_ID_IDX)
        s.run(CREATE_CS_UUID_IDX)
        s.run(CREATE_CS_SLUG_IDX)
        s.run(CREATE_CHUNK_ID_IDX)
        s.run(CREATE_CHUNK_CID_IDX)

# --- Upsert chunk -------------------------------------------------------------

UPSERT_CHUNK = """
MERGE (cs:CaseStudy {case_id: $case_id})
  ON CREATE SET cs.title=$title, cs.url=$url
MERGE (ch:Chunk {chunk_id: $chunk_id})
  SET ch.text=$text,
      ch.order=$order,
      ch.char_start=$start,
      ch.char_end=$end,
      ch.embedding=$embedding
MERGE (cs)-[:HAS_CHUNK]->(ch)
RETURN ch
"""

def upsert_chunk(rec: dict):
    with get_session() as s:
        s.run(UPSERT_CHUNK, **rec)

# --- Retrieval: semantic & full-text -----------------------------------------

FIND_FTS = """
CALL db.index.fulltext.queryNodes('chunk_text_fts', $q) YIELD node, score
RETURN node AS chunk, score
LIMIT $k
"""

FIND_VEC = """
CALL db.index.vector.queryNodes('chunk_vec_idx', $k, $qvec)
YIELD node, score
RETURN node AS chunk, score
"""

def fulltext(q: str, k: int):
    with get_session() as s:
        return s.run(FIND_FTS, q=q, k=k).data()

def vector(qvec: List[float], k: int):
    with get_session() as s:
        return s.run(FIND_VEC, qvec=qvec, k=k).data()

# --- Context fetch for a specific chunk --------------------------------------

GET_CONTEXT = """
MATCH (cs:CaseStudy)-[:HAS_CHUNK]->(c:Chunk {chunk_id:$chunk_id})
RETURN cs.case_id AS case_id,
       cs.title   AS title,
       cs.url     AS url,
       c.chunk_id AS chunk_id,
       c.text     AS text,
       c.order    AS ord,
       c.char_start AS s,
       c.char_end   AS e
"""

def get_context(chunk_id: str):
    with get_session() as s:
        return s.run(GET_CONTEXT, chunk_id=chunk_id).single()

# --- Robust full case study fetch --------------------------------------------

def _assemble_full_text(cs: dict, chunks: List[Dict[str, Any]]) -> str:
    """
    Prefer a stored cs.full_text; otherwise build from chunks ordered by a
    best-effort index: order > chunk_index > index > 0.
    """
    if cs.get("full_text"):
        return cs["full_text"]

    # Sort chunks by any common ordering property
    ordered = sorted(
        (t for t in chunks if t and t.get("t")),
        key=lambda x: x.get("i", 0)
    )
    return "\n".join(t["t"] for t in ordered)

def fetch_case_study_by_ids(
    case_id: Optional[str] = None,
    chunk_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Returns: { id, title, full_text, meta } for a CaseStudy.

    Lookup strategy:
      1) If case_id is provided, try matching on (id, case_id, uuid, slug)
      2) If not found and chunk_id provided, resolve CaseStudy via the Chunk
      3) Build full_text from chunks if not stored on the CaseStudy node
    """

    def _get_by_case_id(tx, cid: str):
        q = """
        MATCH (c:CaseStudy)
        WHERE c.id = $cid OR c.case_id = $cid OR c.uuid = $cid OR c.slug = $cid
        OPTIONAL MATCH (c)-[:HAS_CHUNK]->(ch:Chunk)
        RETURN c AS cs,
               collect({
                   i: coalesce(ch.order, ch.chunk_index, ch.index, 0),
                   t: ch.text
               }) AS chunks
        """
        return tx.run(q, cid=cid).data()

    def _get_by_chunk_id(tx, chid: str):
        q = """
        MATCH (ch:Chunk)
        WHERE ch.id = $chid OR ch.chunk_id = $chid
        MATCH (c:CaseStudy)-[:HAS_CHUNK]->(ch)
        OPTIONAL MATCH (c)-[:HAS_CHUNK]->(all:Chunk)
        RETURN c AS cs,
               collect({
                   i: coalesce(all.order, all.chunk_index, all.index, 0),
                   t: all.text
               }) AS chunks
        """
        return tx.run(q, chid=chid).data()

    rows = []
    with get_session() as s:
        if case_id:
            rows = s.read_transaction(_get_by_case_id, case_id)
        if (not rows or len(rows) == 0) and chunk_id:
            rows = s.read_transaction(_get_by_chunk_id, chunk_id)

    if not rows:
        return None

    cs = rows[0]["cs"]
    chunks: List[Dict[str, Any]] = rows[0].get("chunks") or []

    title = cs.get("title") or cs.get("name") or cs.get("slug") or cs.get("id") or "CaseStudy"
    full_text = _assemble_full_text(cs, chunks)

    return {
        "id": cs.get("id") or cs.get("case_id") or cs.get("uuid") or cs.get("slug"),
        "title": title,
        "full_text": full_text or "",
        "meta": {k: v for k, v in dict(cs).items() if k != "full_text"},
    }

# Backwards-compatible wrapper (used earlier in your app)
def fetch_case_study(case_id: str) -> Optional[Dict[str, Any]]:
    """
    Kept for compatibility. Tries the robust resolver with case_id only.
