# config.py — Tavily-ready configuration
import os
from dotenv import load_dotenv

# Detect Streamlit secrets when running on Streamlit Cloud
try:
    import streamlit as st
    _IN_STREAMLIT = True
    _SECRETS = dict(st.secrets)
except Exception:
    _IN_STREAMLIT = False
    _SECRETS = {}

load_dotenv()

def _get(key, default=None):
    """Read from Streamlit secrets first, then environment, with trimming."""
    val = (_SECRETS.get(key) if isinstance(_SECRETS, dict) else None) or os.getenv(key, default)
    if isinstance(val, str):
        val = val.strip()
    return val

# -----------------------
# OpenAI (required)
# -----------------------
OPENAI_API_KEY = _get("OPENAI_API_KEY", "")
OPENAI_PROJECT_ID = _get("OPENAI_PROJECT_ID")
OPENAI_ORG_ID = _get("OPENAI_ORG_ID")

# Default models (override in Secrets if needed)
EMBED_MODEL = _get("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL  = _get("CHAT_MODEL",  "gpt-4o-mini")

# -----------------------
# Neo4j (required)
# -----------------------
NEO4J_URI      = _get("NEO4J_URI")
NEO4J_USER     = _get("NEO4J_USER")
NEO4J_PASSWORD = _get("NEO4J_PASSWORD")

# -----------------------
# Retrieval tuning
# -----------------------
EMBED_DIM     = int(_get("EMBED_DIM", 1536))
HYBRID_ACCEPT = float(_get("HYBRID_ACCEPT", 0.35))  # raise to 0.55–0.65 for stricter grounding
TOP_K         = int(_get("TOP_K", 8))               # how many candidates to fetch from DB
TOP_N         = int(_get("TOP_N", 3))               # how many to show in UI (if grounded)

# -----------------------
# Web fallback (Tavily)
# -----------------------
# Choose the provider (we default to Tavily). If you later add others, you can switch here.
SEARCH_PROVIDER = _get("SEARCH_PROVIDER", "tavily").lower()

# Tavily credentials and knobs
TAVILY_API_KEY       = _get("TAVILY_API_KEY")
TAVILY_SEARCH_DEPTH  = _get("TAVILY_SEARCH_DEPTH", "basic")  # "basic" (1 credit) or "advanced" (2 credits)
TAVILY_MAX_RESULTS   = int(_get("TAVILY_MAX_RESULTS", 3))    # top N results to consider

# High-level web fallback mode:
# - "tavily": use Tavily if key is present
# - "off":    no live web (return a friendly not-found message)
WEB_FALLBACK_MODE = _get("WEB_FALLBACK_MODE") or (
    "tavily" if (SEARCH_PROVIDER == "tavily" and TAVILY_API_KEY) else "off"
)

# Back-compat flag (some modules may still check this)
WEB_SEARCH_ENABLED = WEB_FALLBACK_MODE != "off"

# -----------------------
# Required keys check
# -----------------------
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
        "OPENAI_API_KEY = sk-proj_...\n"
        "NEO4J_URI = neo4j+s://<your-aura-endpoint>\n"
        "NEO4J_USER = neo4j\n"
        "NEO4J_PASSWORD = <your-password>\n"
        "EMBED_DIM = 1536\n"
        "HYBRID_ACCEPT = 0.35\n"
        "CHAT_MODEL = gpt-4o-mini\n"
        "# Tavily (optional, for live web fallback)\n"
        "SEARCH_PROVIDER = tavily\n"
        "TAVILY_API_KEY = tvly_...\n"
        "TAVILY_SEARCH_DEPTH = basic\n"
        "TAVILY_MAX_RESULTS = 3\n"
    )
    if _IN_STREAMLIT:
        st.error(msg); st.stop()
    else:
        raise AssertionError(msg)
