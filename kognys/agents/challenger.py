# kognys/agents/challenger.py
from langchain_core.prompts import ChatPromptTemplate
from kognys.config import fast_llm
from kognys.graph.state import KognysState
from kognys.utils.transcript import append_entry
from kognys.services.membase_client import query_aip_agent
from typing import AsyncGenerator
from pydantic import BaseModel

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a critical reviewer. Your task is to identify weaknesses in the provided answer "
            "based on the user's question. Look for logical gaps, lack of evidence, or unanswered parts of the question. "
            "Provide a bulleted list of criticisms. If you have no criticisms, return an empty list."
        ),
        ("human", "Question: {question}\n\nDraft Answer:\n{answer}"),
    ]
)

class Criticisms(BaseModel):
    criticisms: list[str]

async def node(state: KognysState) -> AsyncGenerator[dict, None]:
    print("---CHALLENGER: Reviewing the draft for weaknesses...---")
    _structured_llm = fast_llm.with_structured_output(Criticisms)
    _chain = _PROMPT | _structured_llm

    # Get the complete structured response first
    response = await _chain.ainvoke({
        "question": state.validated_question,
        "answer": state.draft_answer
    })
    
    # Stream each criticism as a token for UI feedback
    for criticism in response.criticisms:
        yield {"criticism_token": criticism}

    # CRITICAL: Only yield the final, complete state once at the end
    # This ensures the orchestrator sees the complete list of criticisms
    final_state = {
        "criticisms": response.criticisms,
        "transcript": append_entry(
            state.transcript,
            agent="Challenger",
            action="Generated criticisms",
            output="\n".join(response.criticisms)
        )
    }
    
    yield final_state
