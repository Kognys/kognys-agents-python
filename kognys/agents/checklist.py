# kognys/agents/checklist.py
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

class ChecklistResponse(BaseModel):
    is_sufficient: bool = Field(description="Whether the answer comprehensively addresses the user's question and is ready to be finalized.")
    reasoning: str = Field(description="A brief explanation for the decision.")

# --- THIS IS THE UPDATED PROMPT ---
_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a pragmatic and senior gatekeeper. Your role is to be the final arbiter on whether a research answer is 'good enough' to be sent to the user. \n"
            "Review the draft answer in the context of the original question and the available source documents. \n"
            "Then, review the outstanding criticisms. \n\n"
            "Your decision-making process should be: \n"
            "1. Does the draft answer directly and factually address the user's original question using the provided documents? \n"
            "2. Are the outstanding criticisms asking for information that is impossible to generate from the provided documents (e.g., asking for specific statistics or case studies that are not in the text)? \n\n"
            "If the answer is solid and the criticisms are for 'nice-to-have' information that is not in the source documents, you MUST override the criticisms and set `is_sufficient` to `True`. \n"
            "Only set `is_sufficient` to `False` if the draft answer is factually incorrect, hallucinates information not in the documents, or fails to address the core of the user's question. \n"
            "Respond using the `ChecklistResponse` JSON format."
        ),
        (
            "human",
            "Original Question: {question}\n\n"
            "Available Documents:\n{documents}\n\n"
            "Draft Answer to Evaluate:\n{answer}\n\n"
            "Outstanding Criticisms from another agent:\n{criticisms}"
        ),
    ]
)

_llm = ChatOpenAI(model="gpt-4o", temperature=0) # Use a powerful model for this final decision
_structured_llm = _llm.with_structured_output(ChecklistResponse)
_chain = _PROMPT | _structured_llm

def node(state: KognysState) -> dict:
    if not state.draft_answer:
        return {"is_sufficient": False}

    documents_str = "\n\n".join([doc.get('content', '') for doc in state.documents])
    criticisms_str = "\n".join(state.criticisms) if state.criticisms else "None"
    
    response = _chain.invoke({
        "question": state.validated_question,
        "documents": documents_str,
        "answer": state.draft_answer,
        "criticisms": criticisms_str
    })
    
    print(f"---CHECKLIST AGENT--- \nSufficient: {response.is_sufficient}\nReason: {response.reasoning}\n")
    
    return {"is_sufficient": response.is_sufficient}