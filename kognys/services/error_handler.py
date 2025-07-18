from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def generate_error_response(error_type: str, original_question: str) -> str:
    """
    Uses a GenAI model to create a clear, helpful error message for the user.
    """
    prompt_template = ""
    if error_type == "VALIDATION_FAILED":
        prompt_template = (
            "You are a helpful assistant. The user's research question was rejected because it was too vague or unclear. "
            "Politely explain this and suggest how they could rephrase it to be more specific. "
            "The user's rejected question was: '{question}'"
        )
    elif error_type == "NO_DOCUMENTS_FOUND":
        prompt_template = (
            "You are a helpful research assistant. You were unable to find any information or academic papers about the user's topic. "
            "Politely explain that you couldn't find any sources and suggest they try a different or broader topic. "
            "The topic you searched for was: '{question}'"
        )

    if not prompt_template:
        return "An unexpected error occurred."

    prompt = ChatPromptTemplate.from_template(prompt_template)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
    chain = prompt | llm
    
    response = chain.invoke({"question": original_question})
    return response.content
