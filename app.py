# import streamlit as st
import hmac, streamlit as st # used for password protection of app
from rag.retriever import retrieve_topn
from rag.composer import compose_grounded_answer, web_fallback_answer
from rag.models import AnswerItem, CaseStudy, Chunk
from rag.loader import upload_and_ingest
from rag.store import ensure_indexes
from config import EMBED_DIM, HYBRID_ACCEPT
####################################################
import streamlit.components.v1 as components
from rag.graph_explorer import render_graph_html
####################################################
from rag.store import fetch_case_study
####################################################

# Maintenance gate
if st.secrets.get("MAINTENANCE_MODE", "false").lower() in ("true", "1", "yes"):
    st.set_page_config(page_title="Conexus AI Search")
    st.title("Conexus AI Search")
    st.info(st.secrets.get("MAINTENANCE_MESSAGE", "Temporarily unavailable."))
    st.stop()

def _require_password():
    password = st.secrets.get("APP_PASSWORD", "")
    if not password:
        return  # no password set => skip

    def _check():
        if hmac.compare_digest(st.session_state._pw, password):
            st.session_state._authed = True
        else:
            st.session_state._authed = False

    if st.session_state.get("_authed"):
        return

    st.text_input("Enter password", type="password", key="_pw", on_change=_check)
    if not st.session_state.get("_authed"):
        st.stop()

_require_password()

st.set_page_config(page_title="Conexus AI Search", layout="wide")
st.set_page_config(page_title="Conexus AI Search", page_icon="assets/logo.png", layout="wide")

# Sidebar: Admin
with st.sidebar:
    st.header("Admin")
    if st.button("Ensure Indexes"):
        ensure_indexes(EMBED_DIM)
        st.success("Indexes ensured.")
    st.markdown("---")
    st.header("Upload Case Studies")
    upload_and_ingest()
    st.markdown("---")
    #################################################
    st.subheader("Graph Explorer")
    
    max_nodes = st.slider("Max nodes to visualize", min_value=100, max_value=5000, value=1000, step=100,
                          help="Limits how many nodes are pulled to keep the view responsive.")
    
    if st.button("Render full graph (capped)"):
        with st.spinner("Building graph…"):
            html_path = render_graph_html(max_nodes=max_nodes)
            # Display interactive graph
            with open(html_path, "r", encoding="utf-8") as f:
                components.html(f.read(), height=820, scrolling=True)
    
            # Optional: let admins download the HTML
            with open(html_path, "rb") as fbin:
                st.download_button(
                    "Download graph HTML",
                    data=fbin,
                    file_name="neo4j_graph.html",
                    mime="text/html",
                )
    
    st.caption("Note: This view caps the number of nodes to avoid memory issues on large databases.")
    #################################################


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
        #######################################################

        #########################################################

    st.session_state.history.append({
        "q": user_q,
        "resp": {
            "answer": answer,
            "top3": [i.model_dump() for i in top3_items],
            "grounded_in_db": grounded,
            "external_link": ext_link
        }
    })

# for turn in st.session_state.history:
#     st.chat_message("user").write(turn["q"])
#     with st.chat_message("assistant"):
#         st.write(turn["resp"]["answer"])
#         if turn["resp"]["grounded_in_db"]:
#             st.caption("Grounded in Neo4j (top 3)")
#         else:
#             st.caption("Not found in Neo4j")
#             if turn["resp"].get("external_link"):
#                 st.markdown(f"External source: {turn['resp']['external_link']}")
#         for i, item in enumerate(turn["resp"]["top3"], start=1):
#             with st.expander(f"Source {i}: {item['case_study']['title']} (score {item['score']})"):
#                 st.write(item['chunk']['text'])
#                 st.caption(f"chunk_id={item['chunk']['chunk_id']} range={item['chunk']['char_start']}-{item['chunk']['char_end']} url={item['case_study'].get('url')}")

for t_idx, turn in enumerate(st.session_state.history):
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
                # Show the matching chunk
                st.write(item['chunk']['text'])
                st.caption(
                    f"chunk_id={item['chunk']['chunk_id']} "
                    f"range={item['chunk']['char_start']}-{item['chunk']['char_end']} "
                    f"url={item['case_study'].get('url')}"
                )

                # --- NEW: View full case study button ---
                case_id = item['case_study']['case_id']
                btn_key = f"view_full_{t_idx}_{i}_{case_id}"
                if st.button("View full case study", key=btn_key):
                    data = _get_full_case_study(case_id)
                    if not data or not data.get("full_text"):
                        st.warning("Could not retrieve the full case study.")
                    else:
                        with st.expander(f"Full case study — {data.get('title') or case_id}", expanded=True):
                            st.text(data["full_text"])
                            st.download_button(
                                "Download as .txt",
                                data=data["full_text"].encode("utf-8"),
                                file_name=f"{(data.get('title') or case_id).replace(' ', '_')}.txt",
                                mime="text/plain",
                            )
