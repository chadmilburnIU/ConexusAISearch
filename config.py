# config.py — model/config overrides
import os
from dotenv import load_dotenv
try:
    import streamlit as st
    _IN_STREAMLIT = True
    _SECRETS = dict(st.secrets)
except Exception:
    _IN_STREAMLIT = False
    _SECRETS = {}
load_dotenv()
def _get(key, default=None):
    val = (_SECRETS.get(key) if isinstance(_SECRETS, dict) else None) or os.getenv(key, default)
    if isinstance(val, str): val = val.strip()
    return val
# OpenAI
OPENAI_API_KEY = _get("OPENAI_API_KEY", "")
OPENAI_PROJECT_ID = _get("OPENAI_PROJECT_ID")
OPENAI_ORG_ID = _get("OPENAI_ORG_ID")
# Models (override in Secrets if you like)
EMBED_MODEL = _get("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = _get("CHAT_MODEL", "gpt-4o-mini")  # was 'gpt-5-reasoning' which 404s for many accounts
# Neo4j
NEO4J_URI = _get("NEO4J_URI")
NEO4J_USER = _get("NEO4J_USER")
NEO4J_PASSWORD = _get("NEO4J_PASSWORD")
# Retrieval tuning
EMBED_DIM = int(_get("EMBED_DIM", 1536))
HYBRID_ACCEPT = float(_get("HYBRID_ACCEPT", 0.35))
TOP_K = int(_get("TOP_K", 8))
TOP_N = int(_get("TOP_N", 3))
# Optional feature flags
WEB_SEARCH_ENABLED = _get("WEB_SEARCH_ENABLED", "false").lower() in ("1","true","yes")
REQUIRED = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "NEO4J_URI": NEO4J_URI,
    "NEO4J_USER": NEO4J_USER,
    "NEO4J_PASSWORD": NEO4J_PASSWORD,
}
MISSING = [k for k, v in REQUIRED.items() if not v]
if MISSING:
    msg = (
        "Missing required secrets: " + ", ".join(MISSING) + "\n\n"
        "Add them in Streamlit Cloud → Settings → Secrets. Example:\n\n"
        "OPENAI_API_KEY = sk-...\n"
        "NEO4J_URI = neo4j+s://<your-aura-endpoint>\n"
        "NEO4J_USER = neo4j\n"
        "NEO4J_PASSWORD = <your-password>\n"
        "EMBED_DIM = 1536\n"
        "HYBRID_ACCEPT = 0.35\n"
        "CHAT_MODEL = gpt-4o-mini\n"
    )
    if _IN_STREAMLIT:
        st.error(msg); st.stop()
    else:
        raise AssertionError(msg)
