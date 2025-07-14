# kognys/graph/state.py
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class KognysState(BaseModel):
    question: str
    validated_question: str | None = None

    # future phases
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    draft_answer: str | None = None
    criticisms: List[str] = Field(default_factory=list)
    final_answer: str | None = None
