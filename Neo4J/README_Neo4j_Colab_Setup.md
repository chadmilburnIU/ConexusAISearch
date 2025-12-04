# Conexus AI Search — Neo4j Aura + Google Colab Setup (Non‑Technical)

This guide helps you, step‑by‑step, to:
1. Create a **free Neo4j Aura** database (no install).
2. Save your **URI, user, and password** safely.
3. Use **Google Colab** to load your **PDF case studies** into Neo4j.
4. Verify the data is in Neo4j and ready for the app.

You can do everything in your browser.

---

## Table of Contents
- [What You’ll Need](#what-youll-need)
- [Part 1 — Create a Free Neo4j Aura Instance](#part-1--create-a-free-neo4j-aura-instance)
- [Part 2 — Open the Colab Notebook](#part-2--open-the-colab-notebook)
- [Part 3 — Point the Notebook at Your Neo4j Database](#part-3--point-the-notebook-at-your-neo4j-database)
- [Part 4 — Add Your PDF Case Studies](#part-4--add-your-pdf-case-studies)
- [Part 5 — Run the Notebook to Build the Database](#part-5--run-the-notebook-to-build-the-database)
- [Part 6 — Verify in Neo4j](#part-6--verify-in-neo4j)

---

## What You’ll Need
- A **Google** account (for Google Colab).
- A **free** Neo4j Aura account.

> You do **not** need to install software on your computer.

---

## Part 1 — Create a Free Neo4j Aura Instance
1. Go to **https://console.neo4j.io/** (or via **https://neo4j.com/cloud/platform/aura-graph-database/** → *Get started free*).
2. Sign in (Google or Email).
3. Click **Create Instance** → choose **Free**.
4. Name it (e.g., `Conexus-MRG`) and select a region near you.
5. Click **Create** and wait ~1–2 minutes.

### Save Your Connection Details (Important)
Open your new instance and look at **Connection details**:

- **URI** (encrypted): looks like  
  `bolt+s://xxxxxxxx.databases.neo4j.io:7687`  *(or `neo4j+s://...` — both are OK)*
- **User**: usually `neo4j`
- **Password**: copy and store it when shown the first time.  
  If you don’t have it, click the instance **⋯ → Reset password** and set a new one.

You will use these values in Colab and in the Streamlit app:
```
NEO4J_URI       bolt+s://xxxxxxxx.databases.neo4j.io:7687
NEO4J_USER      neo4j
NEO4J_PASSWORD  your-strong-password
```

---

## Part 2 — Open the Colab Notebook
Use the prebuilt notebook to parse PDFs and load them into Neo4j.

- **Download the notebook** to your computer:  
  **AI Search Conexus Complete Parsing and Loading .ipynb**
- Open **https://colab.research.google.com/**
- Click **File → Upload notebook** and select the file you downloaded.

> Colab may ask to connect to a runtime or access Google Drive later—allow it when prompted.

*(If you need the file again, keep a copy in your repo or Drive so you can reuse it.)*

---

## Part 3 — Point the Notebook at Your Neo4j Database
Near the top of the notebook there is a configuration cell. If you do not see one, add a new code cell and paste the following, replacing with **your** values:

```python
# 🔧 Neo4j connection settings — replace with YOUR values
NEO4J_URI = "bolt+s://xxxxxxxx.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-strong-password"
```

**Test the connection** (use the notebook’s provided test cell if present). If not, add and run this quick check:

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
with driver.session() as s:
    ok = s.run("RETURN 1 AS ok").single()["ok"]
print("Neo4j connection OK:", ok == 1)
```

Expected output: `Neo4j connection OK: True`

---

## Part 4 — Add Your PDF Case Studies
Choose **one** of the options below.

### A) Upload PDFs Directly to Colab (quickest)
1. In Colab’s left sidebar, click the **folder** icon (Files).
2. Click **Upload** and select your PDF files.
3. Put them in a folder, for example: `/content/case_studies`

Then in the notebook set:
```python
PDF_DIR = "/content/case_studies"
```

### B) Use Google Drive (persists between sessions)
1. Mount Drive in the notebook (use the notebook’s “Mount Drive” cell or add):
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
2. Put your PDFs in a Drive folder, e.g.:  
   `/content/drive/My Drive/case_studies`
3. Set in the notebook:
   ```python
   PDF_DIR = "/content/drive/My Drive/case_studies"
   ```

---

## Part 5 — Run the Notebook to Build the Database
Run the notebook cells **top to bottom** (or choose **Runtime → Run all**). The notebook will:

- Read each PDF
- Split it into text **chunks**
- Create **embeddings** (for semantic search)
- Ensure required **indexes**
- Write **CaseStudy** and **Chunk** nodes and relationships into Neo4j

When it finishes, your Neo4j database is populated and ready.

---

## Part 6 — Verify in Neo4j
In the Aura Console, open your instance → **Query**, then run:

```cypher
MATCH (c:CaseStudy)-[:HAS_CHUNK]->(ch:Chunk)
RETURN c.title AS case, count(ch) AS chunks
ORDER BY chunks DESC
LIMIT 10;
```

You should see your case study titles and how many chunks each has.

---


## FAQ
**I lost my Neo4j password—what now?**  
In the Aura Console, open your instance, click **⋯ → Reset password**, and set a new one.

**My URI is `neo4j+s://...` instead of `bolt+s://...`.**  
Either encrypted URI is fine—use what Aura provides. The notebook/app supports both.

**Can I add more PDFs later?**  
Yes. Put them in your chosen folder (Colab or Drive) and re‑run the notebook. It will upsert new case studies and chunks.

**Why don’t I see results in the app?**  
Make sure the notebook ran without errors, indexes were created, and your Neo4j credentials are correct in Streamlit Cloud Secrets.
