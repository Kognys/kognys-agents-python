# kognys/agents/synthesizer.py
from langchain_core.prompts import ChatPromptTemplate
from kognys.config import powerful_llm
from kognys.graph.state import KognysState
from kognys.utils.transcript import append_entry

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
    
    # Handle both string and list content types
    if isinstance(response.content, list):
        # If content is a list, join it or take the first element
        content = " ".join(str(item) for item in response.content) if response.content else ""
    else:
        content = str(response.content)
    
    update_dict = {"draft_answer": content, "criticisms": []}
    
    # Create a safe hash from the content string
    content_hash = hash(content) if content else 0
    
    update_dict["transcript"] = append_entry(
        state.transcript,
        agent="Synthesizer",
        action=f"Drafted answer v{state.revisions+1}",
        output=content_hash
    )
    
    return update_dict