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
    timeout=60,  # 60 second timeout for API calls
    max_retries=2  # Retry failed calls up to 2 times
)

# A more powerful model for complex reasoning and synthesis
powerful_llm = ChatGoogleGenerativeAI(
    model=POWERFUL_LLM_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7,
    timeout=120,  # 120 second timeout for complex reasoning
    max_retries=2  # Retry failed calls up to 2 times
)

print(f"✅ LLM clients initialized. Fast model: {FAST_LLM_MODEL}, Powerful model: {POWERFUL_LLM_MODEL}")

# AIP Agent Configuration
ENABLE_AIP_AGENTS = os.getenv("ENABLE_AIP_AGENTS", "false").lower() == "true"
AIP_AGENT_PREFIX = os.getenv("AIP_AGENT_PREFIX", "kognys")
AIP_USE_ROUTING = os.getenv("AIP_USE_ROUTING", "true").lower() == "true"
AIP_AGENT_TIMEOUT = int(os.getenv("AIP_AGENT_TIMEOUT", "30"))  # seconds

# AIP Agent IDs
AIP_RETRIEVER_ID = f"{AIP_AGENT_PREFIX}-retriever"
AIP_SYNTHESIZER_ID = f"{AIP_AGENT_PREFIX}-synthesizer"
AIP_CHALLENGER_ID = f"{AIP_AGENT_PREFIX}-challenger"
AIP_ORCHESTRATOR_ID = f"{AIP_AGENT_PREFIX}-orchestrator"

if ENABLE_AIP_AGENTS:
    print(f"✅ AIP Agents enabled. Prefix: {AIP_AGENT_PREFIX}, Routing: {AIP_USE_ROUTING}")
