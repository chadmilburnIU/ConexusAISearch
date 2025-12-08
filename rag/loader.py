import streamlit as st
import fitz  # PyMuPDF
from .store import upsert_chunk
from .composer import embed_query

CHARS = 1400
OVERLAP = 200

def _chunks(text: str):
    i = 0; n = len(text)
    while i < n:
        j = min(i+CHARS, n)
        yield text[i:j], i, j
        i += CHARS - OVERLAP if i+CHARS < n else j

def _read_pdf(file) -> str:
    doc = fitz.open(stream=file.read(), filetype="pdf")
    out = []
    for p in doc:
        out.append(p.get_text())
    return "\n".join(out)

def _read_md(file) -> str:
    return file.read().decode("utf-8")

@st.cache_data(show_spinner=False)
def _embed(text: str):
    # Reuse query embedding for MVP
    return embed_query(text)

def upload_and_ingest():
    files = st.file_uploader("Upload PDF or Markdown", type=["pdf","md"], accept_multiple_files=True)
    if not files:
        return
    title = st.text_input("Case Study Title", value="Untitled Case Study")
    url = st.text_input("Source URL (optional)")
    case_id = st.text_input("Case ID", value=title.lower().replace(" ", "-"))
    if st.button("Ingest"):
        for f in files:
            text = _read_pdf(f) if f.type == 'application/pdf' else _read_md(f)
            order = 0
            for chunk, s, e in _chunks(text):
                cid = f"{case_id}-{order:04d}"
                vec = _embed(chunk)
                upsert_chunk({
                    "case_id": case_id,
                    "title": title,
                    "url": url,
                    "chunk_id": cid,
                    "text": chunk,
                    "order": int(order),
                    "start": int(s),
                    "end": int(e),
                    "embedding": vec
                })
                order += 1
        st.success("Ingestion complete.")
