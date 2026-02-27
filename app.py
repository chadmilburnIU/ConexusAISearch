# import streamlit as st
import hmac, streamlit as st # used for password protection of app
from rag.retriever import retrieve_topn
from rag.composer import compose_grounded_answer, web_fallback_answer
from rag.models import AnswerItem, CaseStudy, Chunk
from rag.loader import upload_and_ingest
from rag.store import ensure_indexes
from config import EMBED_DIM, HYBRID_ACCEPT, ADMIN_PASSWORD
####################################################
# these are required to view full graph db if needed
# import streamlit.components.v1 as components
# from rag.graph_explorer import render_graph_html
####################################################
from urllib.parse import urlparse
#####################################################
from config import NEO4J_URI
st.sidebar.caption(f"DEBUG Neo4j URI: {NEO4J_URI}")
#####################################################
def ensure_admin_state():
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False

def admin_login_widget():
    ensure_admin_state()

    with st.sidebar.expander("Admin login", expanded=not st.session_state["is_admin"]):
        if st.session_state["is_admin"]:
            st.success("Admin mode enabled.")
            if st.button("Log out"):
                st.session_state["is_admin"] = False
        else:
            pwd = st.text_input("Admin password", type="password")
            if st.button("Log in"):
                if not ADMIN_PASSWORD:
                    st.warning("Admin password not configured on server.")
                elif pwd == ADMIN_PASSWORD:
                    st.session_state["is_admin"] = True
                    st.success("Admin mode enabled.")
                else:
                    st.error("Incorrect password.")
#####################################################


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

#############################################################
def _normalize_url(u: str | None) -> str | None:
    if not u:
        return None
    return u if urlparse(u).scheme else f"https://{u}"
#############################################################

# Sidebar: Admin
# with st.sidebar:
#     st.header("Admin")
#     if st.button("Ensure Indexes"):
#         ensure_indexes(EMBED_DIM)
#         st.success("Indexes ensured.")
#     st.markdown("---")
#     st.header("Upload Case Studies")
#     upload_and_ingest()
#     st.markdown("---")
# Sidebar: Admin
with st.sidebar:
    st.header("Admin")

    # Show login / logout controls
    admin_login_widget()

    # Only show admin tools if logged in
    if st.session_state.get("is_admin"):
        if st.button("Ensure Indexes"):
            ensure_indexes(EMBED_DIM)
            st.success("Indexes ensured.")

        st.markdown("---")
        st.header("Upload Case Studies")
        upload_and_ingest()
        st.markdown("---")
    else:
        st.info("Admin tools are locked. Please log in above to manage indexes or upload case studies.")

    #################################################
    # This will display full db graph
    # st.subheader("Graph Explorer")
    # max_nodes = st.slider("Max nodes to visualize", min_value=100, max_value=5000, value=1000, step=100,
    #                       help="Limits how many nodes are pulled to keep the view responsive.")
    # if st.button("Render full graph (capped)"):
    #     with st.spinner("Building graph…"):
    #         html_path = render_graph_html(max_nodes=max_nodes)
    #         # Display interactive graph
    #         with open(html_path, "r", encoding="utf-8") as f:
    #             components.html(f.read(), height=820, scrolling=True)
    #         # Optional: let admins download the HTML
    #         with open(html_path, "rb") as fbin:
    #             st.download_button(
    #                 "Download graph HTML",
    #                 data=fbin,
    #                 file_name="neo4j_graph.html",
    #                 mime="text/html",
    #             )
    # st.caption("Note: This view caps the number of nodes to avoid memory issues on large databases.")
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
    # Heuristic: if grounded answer basically says "no info in the data",
    # flip it to not grounded so we don't display sources.
    if grounded:
        ans_lower = answer.lower()
        no_info_phrases = [
            # chunks / case studies
            "the provided chunks do not contain information",
            "the provided chunks do not contain any information",
            "the provided chunks do not include information",
            "no relevant information was found in the provided chunks",
            "the case studies do not contain information",
            "the case studies do not include information",
            # database wording
            "not present in the database",
            "no information regarding",
            "no information about",
        ]

        if any(p in ans_lower for p in no_info_phrases):
            grounded = False


    # top3_items = []
    # for c in (top or [])[:3]:
    #     top3_items.append(AnswerItem(
    #         answer_snippet=c['text'][:220] + ('…' if len(c['text'])>220 else ''),
    #         score=round(float(c['hybrid']), 3),
    #         case_study=CaseStudy(case_id=c['case_id'], title=c['title'], url=c['url']),
    #         chunk=Chunk(chunk_id=c['cid'], text=c['text'], order=int(c['order']),
    #                     char_start=int(c['start']), char_end=int(c['end']))
    #     ))
    # Only show top3 sources when the answer is grounded in the DB
    top3_items = []
    if grounded and top:
        for c in top[:3]:
            top3_items.append(AnswerItem(
                answer_snippet=c['text'][:220] + ('…' if len(c['text']) > 220 else ''),
                score=round(float(c['hybrid']), 3),
                case_study=CaseStudy(case_id=c['case_id'], title=c['title'], url=c['url']),
                chunk=Chunk(
                    chunk_id=c['cid'],
                    text=c['text'],
                    order=int(c['order']),
                    char_start=int(c['start']),
                    char_end=int(c['end']),
                ),
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

# for turn in st.session_state.history:
#     st.chat_message("user").write(turn["q"])
#     with st.chat_message("assistant"):
#         st.write(turn["resp"]["answer"])
#         if turn["resp"]["grounded_in_db"]:
#             st.caption("Grounded in Conexus MRG Case Studies (top 3)")
#         else:
#             st.caption("Not found in Conexus MRG Case Studies")
#             if turn["resp"].get("external_link"):
#                 st.markdown(f"External source: {turn['resp']['external_link']}")
#         for i, item in enumerate(turn["resp"]["top3"], start=1):
#             #with st.expander(f"Source {i}: {item['case_study']['title']} (score {item['score']})"): # SHOW SCORE
#             with st.expander(f"Source {i}: {item['case_study']['title']}"):
#                 # Chunk text
#                 st.write(item['chunk']['text'])

#                 # Metadata (without raw url=...)
#                 st.caption(
#                     f"chunk_id={item['chunk']['chunk_id']} "
#                     f"range={item['chunk']['char_start']}-{item['chunk']['char_end']}"
#                 )

#                 # Clickable link to the case study (opens in a new tab)
#                 url = _normalize_url(item["case_study"].get("url"))
#                 if url:
#                     # Streamlit 1.52 supports link_button; fallback to HTML if anything odd happens
#                     try:
#                         st.link_button("Open case study ↗", url)
#                     except Exception:
#                         st.markdown(
#                             f'<a href="{url}" target="_blank" rel="noopener noreferrer">Open case study ↗</a>',
#                             unsafe_allow_html=True,
#                         )

for turn in st.session_state.history:
    st.chat_message("user").write(turn["q"])
    with st.chat_message("assistant"):
        st.write(turn["resp"]["answer"])

        if turn["resp"]["grounded_in_db"]:
            st.caption("Grounded in Conexus MRG Case Studies (top 3)")

            # Only show sources when grounded
            for i, item in enumerate(turn["resp"]["top3"], start=1):
                with st.expander(f"Source {i}: {item['case_study']['title']}"):
                    st.write(item['chunk']['text'])
                    st.caption(
                        f"chunk_id={item['chunk']['chunk_id']} "
                        f"range={item['chunk']['char_start']}-{item['chunk']['char_end']}"
                    )
                    url = _normalize_url(item["case_study"].get("url"))
                    if url:
                        try:
                            st.link_button("Open case study ↗", url)
                        except Exception:
                            st.markdown(
                                f'<a href="{url}" target="_blank" rel="noopener noreferrer">Open case study ↗</a>',
                                unsafe_allow_html=True,
                            )
        else:
            st.caption("Not found in Conexus MRG Case Studies")
            if turn["resp"].get("external_link"):
                st.markdown(f"External source: {turn['resp']['external_link']}")
            # No source panels in the non-grounded case

