# kognys/agents/input_validator.py

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

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

# 3. Configure the LLM to *always* return JSON matching our Pydantic model
_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
_structured_llm = _llm.with_structured_output(ValidatorResponse)

# 4. Construct the chain using the LCEL pipe syntax
_chain = _PROMPT | _structured_llm


def node(state: KognysState) -> dict:
    """
    Validates the user's question and returns the changes to be merged into the state.
    """
    # Use the chain to get a guaranteed Pydantic object back
    response = _chain.invoke({"question": state.question})

    if not response.approved:
        raise ValueError("Question rejected by validator — ask user to rephrase.")

    # 5. Return a dictionary of the state fields to update
    return {
        "validated_question": response.revised_question or state.question
    }
