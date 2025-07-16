# kognys/agents/checklist.py
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
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
            "You are a pragmatic checklist agent and the final arbiter of quality. Your role is to determine if the research process should conclude. "
            "Critically evaluate the draft answer against the user's original question. "
            "Review the outstanding criticisms, but use your own judgment. If the draft answer is factually correct, comprehensive, and directly answers the user's question, you should approve it, even if there are minor, non-essential criticisms remaining. "
            "For example, if the core answer is solid but a criticism asks for 'more case studies,' you can decide the answer is 'good enough' and set 'is_sufficient' to true. "
            "Only set 'is_sufficient' to false if the answer is factually wrong, incomplete, or fails to address the core of the user's question. "
            "Respond using the `ChecklistResponse` JSON format."
        ),
        (
            "human",
            "Original Question: {question}\n\n"
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
