# kognys/agents/reviser.py
from langchain_core.prompts import ChatPromptTemplate
from kognys.config import fast_llm
from kognys.graph.state import KognysState

# --- PROMPT HAS BEEN UPDATED ---
_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a search query reviser. Your goal is to rewrite a research question into a more effective search query for an academic paper database like OpenAlex. \n"
            "Based on the original question and the criticisms of the failed search, generate a new, concise search query using keywords. \n"
            "IMPORTANT: Respond with ONLY the search query text and nothing else. Do not include conversational phrases like 'Here is the revised query:' or surrounding quotes."
        ),
        (
            "human",
            "Original Question: {question}\n\n"
            "Criticisms of the last retrieval attempt:\n{criticisms}"
        ),
    ]
)


def node(state: KognysState) -> dict:
    """
    Revises the research question into a better search query based on criticisms.
    """
    _chain = _PROMPT | fast_llm


    if not state.criticisms:
        return {}

    criticisms_str = "\n".join(state.criticisms)

    response = _chain.invoke({
        "question": state.question,
        "criticisms": criticisms_str
    })
    
    # Handle both string and list content types
    if isinstance(response.content, list):
        content = " ".join(str(item) for item in response.content) if response.content else ""
    else:
        content = str(response.content)
    
    # The response should now be a clean query string
    new_query = content.strip().strip('"') # Added .strip('"') for safety
    
    print(f"---REVISER AGENT--- \nNew Search Query: {new_query}\n")
    return {"validated_question": new_query, "documents": []}
