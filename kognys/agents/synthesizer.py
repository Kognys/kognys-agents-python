# kognys/agents/synthesizer.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

# This prompt is used for the very first draft, using the full document context.
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

# This new, more efficient prompt is used for all revisions.
# It uses the focused summary instead of the full documents and criticism history.
revision_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a research reviser. Your task is to rewrite the draft answer to fully address the key points "
            "from the provided context summary. The summary contains the most important facts from source documents and the "
            "main criticisms that need to be fixed. Create a new, standalone answer."
        ),
        (
            "human",
            "Context Summary:\n{summary}\n\n"
            "Previous Draft Answer:\n{draft_answer}"
        ),
    ]
)

def node(state: KognysState) -> dict:
    """
    Conditionally synthesizes an initial answer or revises an existing one
    based on a focused context summary.
    """
    # Initialize the LLM client here for robust deployment
    _llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    question = state.validated_question
    documents = state.documents
    draft_answer = state.draft_answer
    context_summary = state.context_summary # Get the summary from the state

    # If a summary exists, it means we are in a revision loop
    if context_summary:
        print("---SYNTHESIZER: Revising draft based on a focused summary...---")
        chain = revision_prompt | _llm
        response = chain.invoke({
            "summary": context_summary,
            "draft_answer": draft_answer,
        })
    # Otherwise, it's the first attempt and we use the full documents
    else:
        print("---SYNTHESIZER: Writing initial draft...---")
        chain = initial_prompt | _llm
        documents_str = "\n\n".join([doc.get('content', '') for doc in documents])
        response = chain.invoke({
            "question": question,
            "documents": documents_str
        })

    # Clear the old criticisms and summary after they've been used
    return {"draft_answer": response.content, "criticisms": [], "context_summary": None}
