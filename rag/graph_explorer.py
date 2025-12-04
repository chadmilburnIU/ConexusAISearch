from __future__ import annotations
from typing import List, Dict
from neo4j import GraphDatabase
from pyvis.network import Network
import json, os, tempfile
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def _first_label(labels: List[str]) -> str:
    return labels[0] if labels else "Node"

def _node_label(props: Dict, labels: List[str]) -> str:
    # Prefer a human title if present, else first label or id
    for k in ("title", "name", "id"):
        if k in props and isinstance(props[k], (str, int, float)):
            return str(props[k])
    return _first_label(labels)

def _tooltip(props: Dict, labels: List[str]) -> str:
    # Pretty JSON tooltip
    return f"<b>{', '.join(labels) or 'Node'}</b><br/><pre style='white-space:pre-wrap'>{json.dumps(props, indent=2)[:4000]}</pre>"

def render_graph_html(max_nodes: int = 1000) -> str:
    """
    Returns a path to a temporary HTML file with the interactive graph.
    Only the first `max_nodes` nodes (ordered by internal id) are included,
    and relationships only between those nodes.
    """
    with driver.session() as s:
        # 1) Pick a node set (cap to avoid OOM on big graphs)
        node_rows = s.run(
            "MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props ORDER BY id(n) LIMIT $limit",
            limit=max_nodes,
        ).data()
        node_ids = [r["id"] for r in node_rows] or [-1]

        # 2) Relationships among those nodes
        rel_rows = s.run(
            """
            MATCH (n)-[r]->(m)
            WHERE id(n) IN $ids AND id(m) IN $ids
            RETURN id(r) AS id, id(n) AS src, id(m) AS dst, type(r) AS type, properties(r) AS props
            """,
            ids=node_ids,
        ).data()

    net = Network(height="780px", width="100%", directed=True, bgcolor="#ffffff")
    net.force_atlas_2based(gravity=-30)

    # Add nodes
    for r in node_rows:
        nid = r["id"]
        labels = r["labels"] or []
        props = r["props"] or {}
        net.add_node(
            nid,
            label=_node_label(props, labels),
            title=_tooltip(props, labels),
            shape="dot",
            size=12,
        )

    # Add edges
    for r in rel_rows:
        net.add_edge(
            r["src"],
            r["dst"],
            label=r["type"],
            title=f"<b>{r['type']}</b><br/><pre style='white-space:pre-wrap'>{json.dumps(r.get('props', {}), indent=2)[:2000]}</pre>",
            arrows="to",
            physics=True,
        )

    # --- FIX: set_options must be JSON, not JS ---
    net.set_options("""
    {
      "nodes": { "font": { "size": 12 } },
      "edges": { "smooth": { "type": "dynamic" } },
      "physics": {
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 200 }
      }
    }
    """)

    # Write tmp HTML and return path
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    tmp.close()
    net.show(tmp.name)
    return tmp.name

