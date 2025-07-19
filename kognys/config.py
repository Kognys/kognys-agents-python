# kognys/config.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Read the necessary variables from the environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FAST_LLM_MODEL = os.getenv("FAST_LLM_MODEL", "gemini-1.5-flash-latest")
POWERFUL_LLM_MODEL = os.getenv("POWERFUL_LLM_MODEL", "gemini-1.5-pro-latest")

# Check if the key exists before creating the clients
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not set in the environment. Please add it to your .env file.")

# 2. Instantiate the LLM clients, passing the API key directly

# A fast model for simple, routine tasks
fast_llm = ChatGoogleGenerativeAI(
    model=FAST_LLM_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.1,
)

# A more powerful model for complex reasoning and synthesis
powerful_llm = ChatGoogleGenerativeAI(
    model=POWERFUL_LLM_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7,
)

print(f"✅ LLM clients initialized. Fast model: {FAST_LLM_MODEL}, Powerful model: {POWERFUL_LLM_MODEL}")
