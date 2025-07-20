# kognys/agents/input_validator.py
import uuid
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from kognys.config import fast_llm
from kognys.graph.state import KognysState
from kognys.utils.transcript import append_entry
import os
from kognys.services.membase_client import create_task, join_task

# 1. Define the desired JSON output structure using Pydantic
class ValidatorResponse(BaseModel):
    """The structured response from the input validator LLM."""
    approved: bool = Field(description="Whether the question is clear, research-worthy, and in scope.")
    revised_question: str = Field(description="A revised, improved version of the question if necessary.")
    rejection_reason: str = Field(description="Detailed explanation of why the question was rejected, if applicable.")

# 2. Define the prompt template
_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a gatekeeper that validates and reformulates user questions. "
            "Your goal is to make questions clear, research-worthy, and in scope. "
            "You must respond using the `ValidatorResponse` JSON format. "
            "If a question is unclear or too broad, provide a reformulated version in the "
            "revised_question field. Only reject questions that are completely out of scope "
            "or cannot be reformulated into a research-worthy question.",
        ),
        ("human", "Validate and reformulate this question: {question}"),
    ]
)


def node(state: KognysState) -> dict:
    """
    Validates the question, creates a unique on-chain task, and joins it.
    """
    _structured_llm = fast_llm.with_structured_output(ValidatorResponse)
    _chain = _PROMPT | _structured_llm
    response = _chain.invoke({"question": state.question})

    # If the question is not approved but we have a revised version, use the revised version
    if not response.approved:
        if response.revised_question:
            # Use the reformulated question instead of rejecting
            print(f"Question reformulated from '{state.question}' to '{response.revised_question}'")
            # Update the state with the reformulated question
            state.question = response.revised_question
        else:
            # Only reject if there's no revised version
            rejection_reason = response.rejection_reason or "Question rejected by validator"
            raise ValueError(rejection_reason)

    # Use uuid.uuid4() to generate a truly random and unique ID for every run.
    unique_id_for_run = str(uuid.uuid4())
    agent_id = os.getenv("MEMBASE_ID")

    # Create and join the on-chain task
    if create_task(task_id=unique_id_for_run):
        join_task(task_id=unique_id_for_run, agent_id=agent_id)

    update_dict = {
        "validated_question": response.revised_question or state.question,
        "paper_id": unique_id_for_run,
        "task_id": unique_id_for_run
    }
    
    update_dict["transcript"] = append_entry(
        state.transcript,
        agent="InputValidator",
        action="Validated question & created on-chain task",
        output=f"Task ID: {unique_id_for_run}"
    )
    
    return update_dict
