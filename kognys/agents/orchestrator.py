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

_llm = ChatOpenAI(model="gpt-4o", temperature=0)
_chain = _PROMPT | _llm

def node(state: KognysState) -> dict:
    """
    Formats the final draft into a polished answer.
    """
    response = _chain.invoke({"answer": state.draft_answer})
    return {"final_answer": response.content}
