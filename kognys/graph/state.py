# kognys/graph/state.py
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class KognysState(BaseModel):
    """
    Represents the shared state of the Kognys research graph.
    Each field is a channel that agents can read from and write to.
    """
    # Initial input
    question: str

    # --- Phase 1: Validation & Retrieval ---
    validated_question: str | None = Field(
        default=None,
        description="The validated and potentially revised question for research."
    )
    documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="A list of retrieved documents from the vector store."
    )

    # --- Phase 2: Chain-of-Debate ---
    draft_answer: str | None = Field(
        default=None,
        description="The initial answer synthesized from the retrieved documents."
    )
    criticisms: List[str] = Field(
        default_factory=list,
        description="A list of criticisms or identified gaps from the ChallengerAgent."
    )
    is_sufficient: bool = Field(
        default=False,
        description="A flag set by the ChecklistAgent indicating if the answer meets all criteria."
    )

    # --- Phase 3 & 4: Finalization ---
    final_answer: str | None = Field(
        default=None,
        description="The final, refined answer after the debate concludes."
    )
