import numpy as np
from typing import List, Dict, Tuple
from config import TOP_K, TOP_N, HYBRID_ACCEPT
from .store import fulltext, vector, get_context
from .composer import embed_query

ALPHA = 0.6  # semantic weight

def normalize(scores: List[float]) -> List[float]:
    if not scores: return []
    a, b = min(scores), max(scores)
    if b - a < 1e-9: return [1.0 for _ in scores]
    return [ (s - a) / (b - a) for s in scores ]

def cos(a, b):
    a = np.array(a); b = np.array(b)
    denom = float(np.linalg.norm(a)*np.linalg.norm(b) + 1e-9)
    return float(np.dot(a,b) / denom)

def mmr(cands: List[Dict], lam: float = 0.7, n: int = TOP_N) -> List[Dict]:
    if not cands: return []
    selected = [cands[0]]
    remaining = cands[1:]
    while len(selected) < n and remaining:
        best_item = None; best_score = -1e9
        for item in remaining:
            sim = max([cos(item['vec'], s['vec']) for s in selected] or [0])
            score = lam*item['hybrid'] - (1-lam)*sim
            if score > best_score:
                best_score, best_item = score, item
        selected.append(best_item)
        remaining = [r for r in remaining if r is not best_item]
    return selected

def retrieve_topn(question: str) -> Tuple[List[Dict], float]:
    qvec = embed_query(question)
    vec_rows = vector(qvec, TOP_K)
    fts_rows = fulltext(question, TOP_K)

    sem_scores = normalize([r['score'] for r in vec_rows])
    lex_scores = normalize([r['score'] for r in fts_rows])

    by_id: Dict[str, Dict] = {}
    for r, s in zip(vec_rows, sem_scores):
        cid = r['chunk']['chunk_id']
        by_id.setdefault(cid, {'sem':0, 'lex':0, 'cid':cid, 'vec':qvec})
        by_id[cid]['sem'] = max(by_id[cid]['sem'], s)
    for r, l in zip(fts_rows, lex_scores):
        cid = r['chunk']['chunk_id']
        by_id.setdefault(cid, {'sem':0, 'lex':0, 'cid':cid, 'vec':qvec})
        by_id[cid]['lex'] = max(by_id[cid]['lex'], l)

    cands = []
    for cid, d in by_id.items():
        rec = get_context(cid)
        if not rec: 
            continue
        hybrid = ALPHA*d['sem'] + (1-ALPHA)*d['lex']
        cands.append({

            'hybrid': hybrid,

            'cid': cid,

            'case_id': rec['case_id'],

            'title': rec['title'],

            'url': rec['url'],

            'text': rec['text'],

            'order': rec['ord'],

            'start': rec['s'],

            'end': rec['e'],

            'vec': qvec

        })

    cands.sort(key=lambda x: x['hybrid'], reverse=True)
    top = mmr(cands, n=TOP_N)
    best = top[0]['hybrid'] if top else 0.0
    return top, best
