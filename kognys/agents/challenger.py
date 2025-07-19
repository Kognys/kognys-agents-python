# kognys/agents/challenger.py
from langchain_core.prompts import ChatPromptTemplate
from kognys.config import fast_llm
from kognys.graph.state import KognysState
from kognys.utils.transcript import append_entry

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

def node(state: KognysState) -> dict:
    """
    Generates criticisms for the draft answer.
    """
    # Configure the LLM to *always* return JSON matching our Pydantic model
    _chain = _PROMPT | fast_llm

    response = _chain.invoke({
        "question": state.validated_question,
        "answer": state.draft_answer
    })
    
    # Simple parsing for now, can be improved with structured output
    criticisms = [c.strip() for c in response.content.split('*') if c.strip()]
    
    update_dict = {"criticisms": criticisms}
    
    update_dict["transcript"] = append_entry(
        state.transcript,
        agent="Challenger",
        action="Provided criticisms",
        details=f"{len(criticisms)} criticism(s)",
        output=criticisms[:2]
    )
    
    return update_dict
