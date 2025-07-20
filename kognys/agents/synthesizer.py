# kognys/agents/synthesizer.py
from langchain_core.prompts import ChatPromptTemplate
from kognys.config import powerful_llm, ENABLE_AIP_AGENTS, AIP_SYNTHESIZER_ID
from kognys.graph.state import KognysState
from kognys.utils.transcript import append_entry
from kognys.services.membase_client import query_aip_agent, send_agent_message

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

def node(state: KognysState) -> dict:
    print("---SYNTHESIZER: Writing/Revising draft...---")
    _chain = _PROMPT | powerful_llm

    documents_str = "\n\n".join([doc.get('content', '') for doc in state.documents])
    criticisms_str = "\n".join(state.criticisms) if state.criticisms else "None"

    response = _chain.invoke({
        "question": state.validated_question,
        "documents": documents_str,
        "criticisms": criticisms_str
    })
    
    draft_answer = response.content
    
    # If AIP is enabled, get additional insights from AIP synthesizer
    if ENABLE_AIP_AGENTS:
        try:
            aip_prompt = f"""Research Question: {state.validated_question}

Draft Answer (version {state.revisions + 1}):
{draft_answer[:1500]}{'...' if len(draft_answer) > 1500 else ''}

Please provide:
1. Key insights that might strengthen this answer
2. Important connections between the sources
3. Suggestions for clarity and coherence

Previous criticisms addressed: {criticisms_str}"""
            
            aip_response = query_aip_agent(
                agent_id=AIP_SYNTHESIZER_ID,
                query=aip_prompt,
                conversation_id=f"research-{state.paper_id}"
            )
            
            if aip_response.get("response"):
                print("---SYNTHESIZER: AIP agent provided enhancement suggestions---")
                # Could integrate suggestions into the draft or store for challenger
                
                # Optionally notify challenger about the synthesis
                if state.revisions > 0:
                    send_agent_message(
                        from_agent_id=AIP_SYNTHESIZER_ID,
                        to_agent_id=AIP_CHALLENGER_ID,
                        action="inform",
                        message=f"Synthesized revision {state.revisions + 1} addressing criticisms"
                    )
                    
        except Exception as e:
            print(f"---SYNTHESIZER: AIP enhancement failed: {e}, continuing with standard synthesis---")
    
    update_dict = {"draft_answer": draft_answer, "criticisms": []}
    
    update_dict["transcript"] = append_entry(
        state.transcript,
        agent="Synthesizer",
        action=f"Drafted answer v{state.revisions+1}",
        output=hash(draft_answer)
    )
    
    return update_dict