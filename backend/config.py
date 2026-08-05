import os
from dotenv import load_dotenv
from groq import Groq

# Initial load from .env file
load_dotenv()

def __getattr__(name):
    if name == "ENABLE_LIVE_SUPPORT":
        val = os.getenv("ENABLE_LIVE_SUPPORT")
        if val is None:
            load_dotenv(override=True)
            val = os.getenv("ENABLE_LIVE_SUPPORT", "true")
        return val.lower() == "true"
    if name == "ENABLE_RAG":
        val = os.getenv("ENABLE_RAG")
        if val is None:
            load_dotenv(override=True)
            val = os.getenv("ENABLE_RAG", "false")
        return val.lower() == "true"
    raise AttributeError(f"module {__name__} has no attribute {name}")

# Initialize Groq client
groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
