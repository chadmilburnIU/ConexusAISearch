from neo4j import GraphDatabase
from typing import List
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_session():
    return driver.session()

CREATE_FTS = "CREATE FULLTEXT INDEX chunk_text_fts IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text]"
CREATE_VEC = "CREATE VECTOR INDEX chunk_vec_idx IF NOT EXISTS FOR (c:Chunk) ON (c.embedding) OPTIONS { indexConfig: {`vector.dimensions`: $dim, `vector.similarity_function`: 'cosine'}}"

def ensure_indexes(dim: int):
    with get_session() as s:
        s.run(CREATE_FTS)
        s.run(CREATE_VEC, dim=dim)

UPSERT_CHUNK = """

MERGE (cs:CaseStudy {case_id: $case_id})
ON CREATE SET cs.title=$title, cs.url=$url
MERGE (ch:Chunk {chunk_id: $chunk_id})
SET ch.text=$text, ch.order=$order, ch.char_start=$start, ch.char_end=$end, ch.embedding=$embedding
MERGE (cs)-[:HAS_CHUNK]->(ch)
RETURN ch
"""

def upsert_chunk(rec: dict):
    with get_session() as s:
        s.run(UPSERT_CHUNK, **rec)

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

GET_CONTEXT = """

MATCH (cs:CaseStudy)-[:HAS_CHUNK]->(c:Chunk {chunk_id:$chunk_id})
RETURN cs.case_id AS case_id, cs.title AS title, cs.url AS url,
       c.chunk_id AS chunk_id, c.text AS text, c.order AS ord,
       c.char_start AS s, c.char_end AS e
"""

def get_context(chunk_id: str):
    with get_session() as s:
        return s.run(GET_CONTEXT, chunk_id=chunk_id).single()





