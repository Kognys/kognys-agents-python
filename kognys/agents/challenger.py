from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

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

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
_chain = _PROMPT | _llm

def node(state: KognysState) -> dict:
    """
    Generates criticisms for the draft answer.
    """
    response = _chain.invoke({
        "question": state.validated_question,
        "answer": state.draft_answer
    })
    
    # Simple parsing for now, can be improved with structured output
    criticisms = [c.strip() for c in response.content.split('*') if c.strip()]
    
    return {"criticisms": criticisms}
