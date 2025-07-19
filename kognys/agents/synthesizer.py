# kognys/agents/synthesizer.py
from langchain_core.prompts import ChatPromptTemplate
from kognys.config import powerful_llm
from kognys.graph.state import KognysState

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
    
    return {"draft_answer": response.content, "criticisms": []}