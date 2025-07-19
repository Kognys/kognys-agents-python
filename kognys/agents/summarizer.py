from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from kognys.graph.state import KognysState

# This prompt instructs the LLM to act as a pre-processor for the main synthesizer
_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a research assistant. Your task is to analyze a collection of source documents and a list of criticisms "
            "about a previous draft answer. Your goal is to create a concise summary of the key points from the documents "
            "that will be most useful for addressing the criticisms. Extract only the most relevant facts, figures, and arguments."
        ),
        (
            "human",
            "Original Question: {question}\n\n"
            "Available Documents:\n{documents}\n\n"
            "Criticisms of the previous draft that need to be addressed:\n{criticisms}"
        ),
    ]
)

def node(state: KognysState) -> dict:
    """
    Summarizes the documents and criticisms to create a focused context
    for the synthesizer agent.
    """
    print("---SUMMARIZER: Creating a focused summary of documents and criticisms...---")
    
    # Initialize the LLM client here for lazy initialization
    _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    _chain = _PROMPT | _llm

    # We don't need to truncate here because the summarizer's job *is* to reduce the context
    documents_str = "\n\n".join([doc.get('content', '') for doc in state.documents])
    criticisms_str = "\n".join(state.criticisms)

    response = _chain.invoke({
        "question": state.validated_question,
        "documents": documents_str,
        "criticisms": criticisms_str
    })
    
    return {"context_summary": response.content}
