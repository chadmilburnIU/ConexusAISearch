from pydantic import BaseModel
from typing import List, Optional

class Chunk(BaseModel):
    chunk_id: str
    text: str
    order: int
    char_start: int
    char_end: int

class CaseStudy(BaseModel):
    case_id: str
    title: str
    url: Optional[str] = None

class AnswerItem(BaseModel):
    answer_snippet: str
    score: float
    case_study: CaseStudy
    chunk: Chunk

class QAResponse(BaseModel):
    answer: str
    top3: List[AnswerItem]
    grounded_in_db: bool
    external_link: Optional[str] = None
