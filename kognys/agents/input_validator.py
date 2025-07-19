# kognys/agents/input_validator.py
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from kognys.config import fast_llm
from kognys.graph.state import KognysState

# 1. Define the desired JSON output structure using Pydantic
class ValidatorResponse(BaseModel):
    """The structured response from the input validator LLM."""
    approved: bool = Field(description="Whether the question is clear, research-worthy, and in scope.")
    revised_question: str = Field(description="A revised, improved version of the question if necessary.")

# 2. Define the prompt template
_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a gatekeeper that decides whether a user question is clear, "
            "research-worthy, and in scope. You must respond using the "
            "`ValidatorResponse` JSON format.",
        ),
        ("human", "Validate this question: {question}"),
    ]
)


def node(state: KognysState) -> dict:
    """
    Validates the user's question and returns the changes to be merged into the state.
    """

    # Configure the LLM to *always* return JSON matching our Pydantic model
    _structured_llm = fast_llm.with_structured_output(ValidatorResponse)

    # Construct the chain
    _chain = _PROMPT | _structured_llm

    # Use the chain to get a guaranteed Pydantic object back
    response = _chain.invoke({"question": state.question})

    if not response.approved:
        raise ValueError("Question rejected by validator — ask user to rephrase.")

    # 5. Return a dictionary of the state fields to update
    return {
        "validated_question": response.revised_question or state.question
    }
