# kognys/agents/synthesizer.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

# 1. Define the prompt
_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a research synthesizer. Your task is to write a clear, concise answer "
            "to the user's question based *only* on the provided documents. "
            "Cite your sources using the 'score' from the document metadata."
        ),
        ("human", "Question: {question}\n\nDocuments:\n{documents}"),
    ]
)

# 2. Configure the LLM
_llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 3. Construct the chain
_chain = _PROMPT | _llm

def node(state: KognysState) -> dict:
    """
    Synthesizes an initial answer from the retrieved documents.
    """
    documents_str = "\n\n".join(
        [f"Content: {doc['content']} (Score: {doc['score']:.2f})" for doc in state.documents]
    )
    
    response = _chain.invoke({
        "question": state.validated_question,
        "documents": documents_str
    })
    
    return {"draft_answer": response.content}
