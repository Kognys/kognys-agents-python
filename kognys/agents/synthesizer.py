# kognys/agents/synthesizer.py
from langchain_core.prompts import ChatPromptTemplate
from kognys.config import powerful_llm, ENABLE_AIP_AGENTS, AIP_SYNTHESIZER_ID, AIP_CHALLENGER_ID
from kognys.graph.state import KognysState
from kognys.utils.transcript import append_entry
from kognys.services.membase_client import query_aip_agent, send_agent_message
from typing import AsyncGenerator

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a Research Synthesizer. Based ONLY on the provided documents, write a comprehensive answer to the user's question. "
            "If criticisms from a previous attempt are provided, you MUST address them in your new draft. "
            "If the documents do not contain information to address a point, explicitly state that the information is not available in the provided sources."
        ),
        (
            "human",
            "User's Question: {question}\n\n"
            "Source Documents:\n{documents}\n\n"
            "Criticisms of Previous Draft (if any):\n{criticisms}"
        ),
    ]
)

async def node(state: KognysState) -> AsyncGenerator[dict, None]:
    print("---SYNTHESIZER: Writing/Revising draft...---")
    _chain = _PROMPT | powerful_llm

    documents_str = "\n\n".join([doc.get('content', '') for doc in state.documents])
    criticisms_str = "\n".join(state.criticisms) if state.criticisms else "None"

    # Stream the response token by token asynchronously for UI
    full_response = ""
    async for token in _chain.astream({
        "question": state.validated_question,
        "documents": documents_str,
        "criticisms": criticisms_str
    }):
        # Yield each token as a partial update for streaming UI
        yield {"draft_answer_token": token.content}
        full_response += token.content

    # CRITICAL: Only yield the final, complete state once at the end
    # This ensures the orchestrator sees the complete draft for decision-making
    final_state = {
        "draft_answer": full_response, 
        "criticisms": [],  # Reset criticisms when new draft is created
        "transcript": append_entry(
            state.transcript,
            agent="Synthesizer",
            action=f"Drafted answer v{state.revisions+1}",
            output=hash(full_response)
        )
    }
    
    yield final_state