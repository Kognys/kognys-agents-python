# kognys/agents/reviser.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a search query reviser. You receive a research question and criticisms about why "
            "the current answer is failing. Your task is to rewrite the original question into a better, "
            "more effective search query to find the correct documents. Do not be conversational."
        ),
        (
            "human",
            "Original Question: {question}\n\n"
            "Criticisms of the current answer attempt:\n{criticisms}"
        ),
    ]
)

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
_chain = _PROMPT | _llm

def node(state: KognysState) -> dict:
    """
    Revises the research question based on criticisms.
    """
    if not state.criticisms:
        return {}

    criticisms_str = "\n".join(state.criticisms)

    response = _chain.invoke({
        "question": state.question,
        "criticisms": criticisms_str
    })
    
    print(f"---REVISER AGENT--- \nNew Question: {response.content}\n")
    return {"validated_question": response.content, "documents": []}
