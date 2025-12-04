# Neo4j Q&A Copilot — OpenAI Web Search Tool

## What’s in here?
- Streamlit app with chat and unlimited follow-ups.
- Hybrid retrieval (Neo4j **vector + full‑text**) → MMR → top‑3 sources (case study + chunk IDs).
- Grounded response composer.

- **Fallback** uses OpenAI **Responses API web_search tool** — no extra keys (only your OpenAI key).

- Uploader for PDFs/Markdown that chunks + embeds + upserts into Neo4j.


## Run locally
1) `cp .env.example .env` and fill: `OPENAI_API_KEY`, `NEO4J_*`

2) `pip install -r requirements.txt`

3) `streamlit run app.py`

4) Sidebar → **Ensure Indexes** → Upload files → Ask questions


## Deploy on Streamlit Cloud
- Set secrets in the app’s Settings → Secrets:

  `OPENAI_API_KEY`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `EMBED_DIM=1536`, `HYBRID_ACCEPT=0.35`

- No other keys are required.

