# kognys/graph/state.py
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class KognysState(BaseModel):
    """
    Represents the shared state of the Kognys research graph.
    Each field is a channel that agents can read from and write to.
    """
    # --- Input and Core State ---
    question: str
    paper_id: str | None = Field(default=None, description="The unique, content-addressable ID for the final paper.")

    # --- Research and Debate Loop State ---
    validated_question: str | None = Field(
        default=None,
        description="The validated and potentially revised question for research."
    )
    documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="A list of retrieved documents from the vector store."
    )
    retrieval_status: str | None = Field(
        default=None,
        description="A message indicating the status of the document retrieval."
    )
    draft_answer: str | None = Field(
        default=None,
        description="The current draft answer being debated."
    )
    criticisms: List[str] = Field(
        default_factory=list,
        description="A list of criticisms for the current draft."
    )
    revisions: int = Field(
        default=0, 
        description="A counter for how many revision cycles have occurred."
    )

    # --- Final Output ---
    final_answer: str | None = Field(
        default=None,
        description="The final, conclusive answer produced by the Orchestrator."
    )