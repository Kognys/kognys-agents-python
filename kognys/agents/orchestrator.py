# kognys/agents/orchestrator.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a final editor and orchestrator. Your task is to take a validated research draft "
            "and format it into a clean, well-structured final answer. Do not add new information. "
            "Focus on clarity, formatting, and presentation."
        ),
        ("human", "Draft Answer:\n{answer}"),
    ]
)

_llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
_chain = _PROMPT | _llm

def node(state: KognysState) -> dict:
    """
    Conditionally formats the final answer OR a "cannot answer" message.
    """
    # If retrieval failed, there will be no draft answer.
    if state.retrieval_status == "No documents found":
        print("---ORCHESTRATOR: No documents found to generate an answer.---")
        return {"final_answer": "I am sorry, but I could not find any relevant information in the knowledge base to answer your question."}
    
    # Otherwise, format the successful draft as before
    print("---ORCHESTRATOR: Formatting final answer.---")
    response = _chain.invoke({"answer": state.draft_answer})
    return {"final_answer": response.content}
