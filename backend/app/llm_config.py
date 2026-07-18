"""
Single place that decides which LLM the whole app uses.

To switch providers: change LLM_PROVIDER in .env (and make sure the matching
API key is set). Nothing else in the codebase needs to change because every
agent calls get_llm() instead of importing a specific provider directly.
"""

from functools import lru_cache
from app.config import settings


@lru_cache(maxsize=1)
def get_llm():
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set in .env")

        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
            convert_system_message_to_human=True,
        )

    elif provider == "groq":
        from langchain_groq import ChatGroq

        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set in .env")

        return ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.3,
        )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Use 'gemini' or 'groq'."
        )
