# Unified secrets loader: Streamlit Cloud (st.secrets) or local .env
import os
try:
    import streamlit as st
    _S = st.secrets  # on Streamlit Cloud
except Exception:
    _S = {}
from dotenv import load_dotenv
load_dotenv()

def _get(key, default=None):
    return (_S.get(key) if isinstance(_S, dict) else None) or os.getenv(key, default)

OPENAI_API_KEY = _get("OPENAI_API_KEY")
NEO4J_URI = _get("NEO4J_URI")
NEO4J_USER = _get("NEO4J_USER")
NEO4J_PASSWORD = _get("NEO4J_PASSWORD")

EMBED_DIM = int(_get("EMBED_DIM", 1536))
HYBRID_ACCEPT = float(_get("HYBRID_ACCEPT", 0.35))
TOP_K = int(_get("TOP_K", 8))
TOP_N = int(_get("TOP_N", 3))

assert OPENAI_API_KEY, "Missing OPENAI_API_KEY"
assert NEO4J_URI and NEO4J_USER and NEO4J_PASSWORD, "Missing Neo4j connection env vars"
