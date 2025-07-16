# kognys/agents/synthesizer.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

# Create two different prompts: one for the initial draft, and one for revising.
initial_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a research synthesizer. Your task is to write a clear, concise answer "
            "to the user's question based *only* on the provided documents. "
            "Cite your sources using the 'score' from the document metadata where appropriate."
        ),
        ("human", "Question: {question}\n\nDocuments:\n{documents}"),
    ]
)

revision_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a research reviser. Your task is to rewrite the draft answer to fully address the provided "
            "criticisms. Use the original documents as evidence. The revised answer should be a complete, "
            "standalone piece of text. Do not just address the criticisms directly, but integrate the "
            "feedback into a new and improved version of the answer."
        ),
        (
            "human",
            "Original Question: {question}\n\n"
            "Original Documents:\n{documents}\n\n"
            "Previous Draft Answer:\n{draft_answer}\n\n"
            "Criticisms to Address:\n{criticisms}"
        ),
    ]
)

# Make sure to define your LLM instance here
_llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# The chains are now separate
initial_chain = initial_prompt | _llm
revision_chain = revision_prompt | _llm

def node(state: KognysState) -> dict:
    """
    Conditionally synthesizes or revises an answer based on the graph state.
    """
    question = state.validated_question
    documents = state.documents
    draft_answer = state.draft_answer
    criticisms = state.criticisms

    documents_str = "\n\n".join(
        [f"Content: {doc['content']} (Score: {doc['score']:.2f})" for doc in documents]
    )

    if criticisms:
        print("---SYNTHESIZER: Revising draft based on criticisms...---")
        response = revision_chain.invoke({
            "question": question,
            "documents": documents_str,
            "draft_answer": draft_answer,
            "criticisms": "\n".join(criticisms)
        })
    else:
        print("---SYNTHESIZER: Writing initial draft...---")
        response = initial_chain.invoke({
            "question": question,
            "documents": documents_str
        })

    return {"draft_answer": response.content, "criticisms": []}
