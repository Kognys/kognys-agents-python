# kognys/agents/checklist.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

# 1. Define the desired output structure
class ChecklistResponse(BaseModel):
    """A structured response from the Checklist Agent."""
    is_sufficient: bool = Field(description="Whether the answer comprehensively addresses the user's question based on the provided documents and criticisms.")
    reasoning: str = Field(description="A brief explanation for the decision.")

# 2. Define the prompt
_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a meticulous checklist agent. Your role is to determine if the research process should conclude. "
            "Evaluate the draft answer against the original question and the outstanding criticisms. "
            "If the answer is complete, comprehensive, and all criticisms have been addressed, set 'is_sufficient' to true. "
            "Otherwise, set it to false. Respond using the `ChecklistResponse` JSON format."
        ),
        (
            "human",
            "Original Question: {question}\n\n"
            "Retrieved Documents:\n{documents}\n\n"
            "Draft Answer:\n{answer}\n\n"
            "Outstanding Criticisms:\n{criticisms}"
        ),
    ]
)

# 3. Configure a structured-output LLM
_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
_structured_llm = _llm.with_structured_output(ChecklistResponse)

# 4. Construct the chain
_chain = _PROMPT | _structured_llm

def node(state: KognysState) -> dict:
    """
    Checks if the draft answer is sufficient to end the debate loop.
    """
    if not state.draft_answer:
        return {"is_sufficient": False}

    documents_str = "\n\n".join([doc['content'] for doc in state.documents])
    criticisms_str = "\n".join(state.criticisms) if state.criticisms else "None"
    
    response = _chain.invoke({
        "question": state.validated_question,
        "documents": documents_str,
        "answer": state.draft_answer,
        "criticisms": criticisms_str
    })
    
    print(f"---CHECKLIST AGENT--- \nSufficient: {response.is_sufficient}\nReason: {response.reasoning}\n")
    
    return {"is_sufficient": response.is_sufficient}
