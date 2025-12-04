from typing import List, Optional, Tuple
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Embeddings ---
def embed_query(q: str) -> List[float]:
    emb = client.embeddings.create(model="text-embedding-3-small", input=q)
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

    res = client.chat.completions.create(model="gpt-5-reasoning", messages=messages)

    return res.choices[0].message.content

# --- Web fallback using OpenAI Responses API web_search tool ---
def web_fallback_answer(question: str) -> Tuple[str, Optional[str]]:

    try:

        res = client.responses.create(

            model="gpt-5-reasoning",

            input=question,

            tools=[{"type": "web_search"}],

            tool_choice="auto"

        )

        # Generic extraction: prefer output_text if present

        answer_text = getattr(res, "output_text", None)

        if not answer_text:

            # Fallback to a minimal parse of content blocks

            try:

                blocks = getattr(res, "output", []) or []

                parts = []

                for b in blocks:


                    txt = getattr(b, "text", None) or getattr(getattr(b, "content", None), "0", None)

                    if txt:

                        parts.append(str(txt))

                answer_text = "\n".join(parts) if parts else "Answer generated from web search."

            except Exception:

                answer_text = "Answer generated from web search."


        # Try to find a cited URL if available

        cited_url = None

        try:

            # Some SDK versions expose citations under res.output or res.annotations

            for b in (getattr(res, "output", []) or []):

                urls = getattr(b, "urls", None)

                if urls:

                    cited_url = urls[0]

                    break

        except Exception:

            pass

        return (f"Not found in Neo4j. Based on the web: {answer_text}", cited_url)

    except Exception:

        # If web_search tool isn't enabled on the account, degrade gracefully

        return ("Not found in Neo4j. Web search is unavailable for this key.", None)

