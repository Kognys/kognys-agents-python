# kognys/agents/input_validator.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a gatekeeper that decides whether a user question is clear, "
     "research-worthy, and in scope. "
     "Return JSON: {approved: bool, revised_question: string}."),
    ("human", "{question}")
])

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

def node(state: KognysState, **_) -> KognysState:
    resp = _llm.invoke(_PROMPT.format(question=state.question))
    data = resp.json() if isinstance(resp, str) else resp
    if not data.get("approved", False):
        raise ValueError("Question rejected by validator — ask user to rephrase.")
    state.validated_question = data.get("revised_question") or state.question
    return state
