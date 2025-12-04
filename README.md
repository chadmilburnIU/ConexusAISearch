# Conexus AI Search (Proof‑of‑Concept)

A simple Streamlit app that lets you **ask natural‑language questions** and returns answers grounded in your organization’s **Conexus MRG case studies**. It also includes an **Admin** sidebar to upload new PDFs and visualize your Neo4j graph.

> This README is written for non‑technical users. You can deploy the app on **Streamlit Community Cloud** with only a few secrets (keys) and no local installs.

---

## What you’ll see in the app

- A chat box where you ask a question.
- An answer that is *grounded* in your case studies, followed by a list of **top sources**. Expanding a source shows the exact text snippet used, plus a link to the originating case study (when available).
- In the **Admin** sidebar:
  - **Ensure Indexes**: creates Neo4j search indexes (run the first time you deploy).
  - **Upload Case Studies**: drag‑and‑drop PDF files to add them to the database.
  - **Graph Explorer**: render a capped, interactive view of your database to inspect nodes and relationships.

> The Graph Explorer writes a temporary HTML file and shows it inside the app using an interactive PyVis view (nodes + edges + physics). fileciteturn0file8

---

## How answers are selected (plain English)

When you ask a question, the app searches the case‑study database in two ways and blends the results:

1. **Semantic similarity** (vector search): checks which chunks of text *mean* something similar to your question.
2. **Keyword match** (full‑text search): finds chunks that contain the words you used.

The app combines both signals and shows the best‑matching sources (by default the **top 3**). The final answer is composed using the highest‑ranked snippets as grounding, so you can **verify** where the answer came from by opening each source.

---

## One‑click deployment on Streamlit Community Cloud

1. **Fork** this GitHub repo into your own account.
2. Go to **https://streamlit.io/cloud** → **New app** → choose your repo and set **Main file** to `app.py`.
3. In the “**Advanced settings → Secrets**” section, paste the following template and fill in your values:

```yaml
# Streamlit secrets (Settings → Advanced → Secrets)

# Required – your OpenAI and Neo4j credentials
OPENAI_API_KEY: "sk-proj-..."
NEO4J_URI: "neo4j+s://<your-db-host>:7687"
NEO4J_USER: "neo4j"
NEO4J_PASSWORD: "<your-password>"

# Optional – simple app gate
APP_PASSWORD: "<set a password for the app users>"

# Optional – maintenance banner
MAINTENANCE_MODE: "false"        # set to "true" to take the app offline
MAINTENANCE_MESSAGE: "Conexus AI Search is undergoing maintenance."
```

4. Click **Deploy**. Streamlit will install everything from `requirements.txt` automatically.
5. Open the app. In the left **Admin** panel, click **Ensure Indexes** once to prepare the database.

> **Tip:** You can change the app name/icon later in Streamlit Cloud’s settings.

---

## Loading new case studies (PDFs)

1. Open the app and go to the left **Admin** panel.
2. In **Upload Case Studies**, drag‑and‑drop one or more PDF files.
3. The app automatically
   - splits each PDF into readable *chunks*,
   - generates AI embeddings (needed for semantic search), and
   - stores the chunks in Neo4j, linking them to a case‑study record.

After upload finishes, your new content is immediately searchable. Ask a question that should match the document and confirm the snippets look correct.

---

## Optional: Visualize the database

In **Admin → Graph Explorer** you can render a capped, interactive view of your graph to see how **CaseStudy** and **Chunk** nodes are connected. Click **Render full graph (capped)** to generate and view an interactive HTML. (This is capped to keep the view responsive.) fileciteturn0file8

---

## Day‑to‑day use

1. Type a question in the chat box (for example: “How can we minimize production downtime during installation?”).
2. Read the answer.
3. Expand the **Source 1 / Source 2 / …** panels to see the supporting text and, when available, click the link to the original case study.

> Depending on configuration, you may be able to change how many sources are shown (e.g., top 3 vs top 10) from the sidebar. Showing more sources gives you more context but can take slightly longer.

---

## Managing access & maintenance

- **Password gate**: If `APP_PASSWORD` is set in Secrets, users will be prompted for a password before they can use the app.
- **Maintenance mode**: Set `MAINTENANCE_MODE` to `"true"` in Secrets to temporarily take the app offline and show your `MAINTENANCE_MESSAGE` instead of the chat UI.

---

## Troubleshooting

- **“Missing OPENAI_API_KEY/Neo4j credentials”**: Make sure you pasted the Secrets correctly in Streamlit Cloud.
- **“Invalid API key”**: Double‑check your OpenAI key begins with `sk-proj-` and is active.
- **Graph view won’t render**: The graph is capped for performance. Try reducing the node cap in the sidebar and rendering again. fileciteturn0file8
- **No results**: Ensure you’ve uploaded at least one PDF and clicked **Ensure Indexes** once after first deployment.

---

## What’s inside (for the curious)

- **`app.py`** – Streamlit UI and chat flow.
- **`retriever.py`** – Blends semantic and keyword search to find the best supporting chunks.
- **`composer.py`** – Composes the final grounded answer using those chunks.
- **`loader.py`** – PDF ingestion (chunking + embedding) and write‑back to Neo4j.
- **`store.py`** – Neo4j queries and index creation.
- **`graph_explorer.py`** – Generates the interactive PyVis HTML for the Admin graph view. fileciteturn0file8
- **`config.py`** – Central place for environment variables and tunables.
- **`requirements.txt`** – Python libraries; Streamlit Cloud installs these automatically.

---

## Support

If you get stuck, open an issue in the GitHub repo with a short description and a screenshot of any error you see.
