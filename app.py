import streamlit as st
from rag.retriever import retrieve_topn
from rag.composer import compose_grounded_answer, web_fallback_answer
from rag.models import AnswerItem, CaseStudy, Chunk
from rag.loader import upload_and_ingest
from rag.store import ensure_indexes
from config import EMBED_DIM, HYBRID_ACCEPT

st.set_page_config(page_title="Conexus AI Search", layout="wide")
st.set_page_config(page_title="Conexus AI Search", page_icon="assets/conexus.svg", layout="wide")

# Sidebar: Admin
with st.sidebar:
    st.header("Admin")
    if st.button("Ensure Indexes"):
        ensure_indexes(EMBED_DIM)
        st.success("Indexes ensured.")
    st.markdown("---")
    st.header("Upload Case Studies")
    upload_and_ingest()

# Chat panel
st.title("Conexus AI Search")
if "history" not in st.session_state:
    st.session_state.history = []

user_q = st.chat_input("Ask about the case studies…")
if user_q:
    top, best = retrieve_topn(user_q)
    if top and best >= HYBRID_ACCEPT:
        answer = compose_grounded_answer(user_q, top)
        grounded = True
        ext_link = None
    else:
        answer, ext_link = web_fallback_answer(user_q)
        grounded = False

    top3_items = []
    for c in (top or [])[:3]:
        top3_items.append(AnswerItem(
            answer_snippet=c['text'][:220] + ('…' if len(c['text'])>220 else ''),
            score=round(float(c['hybrid']), 3),
            case_study=CaseStudy(case_id=c['case_id'], title=c['title'], url=c['url']),
            chunk=Chunk(chunk_id=c['cid'], text=c['text'], order=int(c['order']), char_start=int(c['start']), char_end=int(c['end']))
        ))

    st.session_state.history.append({
        "q": user_q,
        "resp": {
            "answer": answer,
            "top3": [i.model_dump() for i in top3_items],
            "grounded_in_db": grounded,
            "external_link": ext_link
        }
    })

for turn in st.session_state.history:
    st.chat_message("user").write(turn["q"])
    with st.chat_message("assistant"):
        st.write(turn["resp"]["answer"])
        if turn["resp"]["grounded_in_db"]:
            st.caption("Grounded in Neo4j (top 3)")
        else:
            st.caption("Not found in Neo4j")
            if turn["resp"].get("external_link"):
                st.markdown(f"External source: {turn['resp']['external_link']}")
        for i, item in enumerate(turn["resp"]["top3"], start=1):
            with st.expander(f"Source {i}: {item['case_study']['title']} (score {item['score']})"):
                st.write(item['chunk']['text'])
                st.caption(f"chunk_id={item['chunk']['chunk_id']} range={item['chunk']['char_start']}-{item['chunk']['char_end']} url={item['case_study'].get('url')}")
