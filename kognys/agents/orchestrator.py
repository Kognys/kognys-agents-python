# kognys/agents/orchestrator.py
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from kognys.config import powerful_llm
import os
from kognys.graph.state import KognysState
from kognys.utils.transcript import append_entry
from kognys.services.membase_client import query_aip_agent
from typing import AsyncGenerator

class OrchestratorResponse(BaseModel):
    decision: str = Field(description="The next action. Must be one of: 'REVISE', 'RESEARCH_AGAIN', or 'FINALIZE'.")
    explanation: str = Field(description="A brief justification for the decision.")
    next_query: str | None = Field(default=None, description="The new search query, ONLY if the decision is 'RESEARCH_AGAIN'.")
    final_answer: str | None = Field(default=None, description="The final answer, ONLY if the decision is 'FINALIZE'.")

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are the Orchestrator, the Editor-in-Chief of a research process. Your role is to analyze the state of the debate and decide the most strategic next step to reach a conclusion efficiently. You have access to a `revision_count`. \n\n"
            "1. **Analyze the Criticisms:** Review the criticisms in the context of the available source documents. \n"
            "2. **Make a Strategic Decision:** \n"
            "   - If the criticisms point to important information that IS present in the documents but was missed, choose `REVISE`. \n"
            "   - If the criticisms highlight a fundamental lack of information AND the `revision_count` is low (less than 2), choose `RESEARCH_AGAIN` and formulate a new, improved search query. \n"
            "   - If the `revision_count` is 2 or more, OR if the criticisms are for details not present in the sources, the debate has reached the point of diminishing returns. Choose `FINALIZE`. You must then write the final answer yourself, incorporating the best parts of the last draft and explicitly acknowledging the valid, un-addressable limitations from the criticisms (e.g., 'Based on the available sources, specific case studies were not found...'). \n\n"
            "You must respond using the `OrchestratorResponse` JSON format."
        ),
        (
            "human",
            "Revision Count: {revisions}\n\n"
            "Original Question: {question}\n\n"
            "Available Source Documents:\n{documents}\n\n"
            "Current Draft Answer:\n{answer}\n\n"
            "Outstanding Criticisms:\n{criticisms}"
        ),
    ]
)

async def node(state: KognysState) -> AsyncGenerator[dict, None]:
    print("---ORCHESTRATOR: Moderating the debate and deciding next step...---")
    _structured_llm = powerful_llm.with_structured_output(OrchestratorResponse)
    _chain = _PROMPT | _structured_llm

    # Handle the case where retrieval fails and we come here directly
    if state.retrieval_status == "No documents found":
        final_state = {
            "final_answer": "I am sorry, but I could not find any relevant information to answer your question.",
            "transcript": append_entry(
                state.transcript,
                agent="Orchestrator",
                action="Made decision",
                output="No documents found"
            )
        }
        yield final_state
        return
    
    documents_str = "\n\n".join([doc.get('content', '') for doc in state.documents])
    criticisms_str = "\n".join(state.criticisms) if state.criticisms else "None"
    
    # Get the complete decision first
    response = await _chain.ainvoke({
        "revisions": state.revisions,
        "question": state.validated_question,
        "documents": documents_str,
        "answer": state.draft_answer,
        "criticisms": criticisms_str
    })
    
    print(f"---ORCHESTRATOR DECISION: {response.decision} ---\nReason: {response.explanation}")

    if response.decision == "RESEARCH_AGAIN":
        final_state = {
            "validated_question": response.next_query, 
            "documents": [], 
            "revisions": state.revisions + 1,
            "transcript": append_entry(
                state.transcript,
                agent="Orchestrator",
                action="Made decision",
                output=response.decision
            )
        }
        yield final_state
        
    elif response.decision == "FINALIZE":
        # Stream the final answer token by token for UI
        full_final_answer = ""
        async for token in powerful_llm.astream(response.final_answer):
             yield {"final_answer_token": token.content}
             full_final_answer += token.content
        
        # Yield the complete final state
        final_state = {
            "final_answer": full_final_answer,
            "transcript": append_entry(
                state.transcript,
                agent="Orchestrator",
                action="Made decision",
                output=response.decision
            )
        }
        yield final_state
        
    else:  # REVISE
        final_state = {
            "revisions": state.revisions + 1,
            "transcript": append_entry(
                state.transcript,
                agent="Orchestrator",
                action="Made decision",
                output=response.decision
            )
        }
        yield final_state
