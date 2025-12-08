from typing import List, Optional, Tuple
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_PROJECT_ID, OPENAI_ORG_ID, CHAT_MODEL, EMBED_MODEL, WEB_SEARCH_ENABLED

client = OpenAI(
    api_key=OPENAI_API_KEY,
    project=OPENAI_PROJECT_ID if OPENAI_PROJECT_ID else None,
    organization=OPENAI_ORG_ID if OPENAI_ORG_ID else None,
)

# --- Embeddings ---
def embed_query(q: str) -> List[float]:
    emb = client.embeddings.create(model=EMBED_MODEL, input=q)
    return emb.data[0].embedding

# --- Answer composition (grounded) ---
PROMPT = """

You are a helpful analyst. Answer the user's question using ONLY the provided chunks.

If a fact is not in the chunks, state that it's not present in the database.

Return a concise answer.

"""

def compose_grounded_answer(question: str, chunks: List[dict]) -> str:
    sources = "\n\n".join([

        f"[{i+1}] {c['title']} (chunk {c['cid']} range {c['start']}-{c['end']}):\n{c['text']}" for i,c in enumerate(chunks)

    ])
    messages = [

        {"role": "system", "content": PROMPT},

        {"role": "user", "content": f"Question: {question}\n\nSources:\n{sources}"}

    ]

    res = client.chat.completions.create(model=CHAT_MODEL, messages=messages)

    return res.choices[0].message.content

# --- Web fallback (optional) ---
def web_fallback_answer(question: str) -> Tuple[str, Optional[str]]:

    if not WEB_SEARCH_ENABLED:

        # No web search; return general model answer with a disclaimer

        msg = [

            {"role": "system", "content": "Answer generally. If not in local context, say it's not from the database."},

            {"role": "user", "content": question}

        ]

        res = client.chat.completions.create(model=CHAT_MODEL, messages=msg)

        return ("Not found in Neo4j. " + res.choices[0].message.content, None)

    try:

        res = client.responses.create(

            model=CHAT_MODEL,

            input=question,

            tools=[{"type": "web_search"}],

            tool_choice="auto"

        )

        answer_text = getattr(res, "output_text", None) or "Answer generated from web search."

        cited_url = None

        try:

            for b in (getattr(res, "output", []) or []):

                urls = getattr(b, "urls", None)

                if urls:

                    cited_url = urls[0]

                    break

        except Exception:

            pass

        return (f"Not found in Neo4j. Based on the web: {answer_text}", cited_url)

    except Exception:

        # If the tool is not enabled for the key/account

        msg = [

            {"role": "system", "content": "Answer generally. If not in local context, say it's not from the database."},

            {"role": "user", "content": question}

        ]

        res = client.chat.completions.create(model=CHAT_MODEL, messages=msg)

        return ("Not found in Neo4j. " + res.choices[0].message.content, None)

