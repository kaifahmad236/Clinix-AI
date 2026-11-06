"""
Single place that decides which LLM the whole app uses.

Provider selection & automatic fallback:
  - LLM_PROVIDER sets the *primary* provider ("gemini" or "groq").
  - If both GEMINI_API_KEY and GROQ_API_KEY are set, the app will
    automatically fall back to the other provider when the primary one
    raises a rate-limit / quota error (429 / ResourceExhausted).
  - To switch providers manually: change LLM_PROVIDER in .env.
"""

import logging
from functools import lru_cache
from app.config import settings

logger = logging.getLogger(__name__)

# Rate-limit / quota error signals from each provider
_QUOTA_SIGNALS = (
    "429",
    "quota",
    "rate limit",
    "rate_limit",
    "resourceexhausted",
    "too many requests",
)


def _is_quota_error(exc: Exception) -> bool:
    """Return True if the exception looks like a rate-limit / quota error."""
    msg = str(exc).lower()
    return any(signal in msg for signal in _QUOTA_SIGNALS)


def _build_gemini():
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")

    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
        convert_system_message_to_human=True,
    )


def _build_groq():
    from langchain_groq import ChatGroq

    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set")

    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
    )


class _FallbackLLM:
    """
    Thin wrapper that calls the primary LLM and transparently falls back to
    the secondary one on quota / rate-limit errors.  Implements the same
    interface that LangChain agents expect (invoke / stream / ainvoke).
    """

    def __init__(self, primary, secondary, secondary_name: str):
        self._primary = primary
        self._secondary = secondary
        self._secondary_name = secondary_name

    # ------------------------------------------------------------------ #
    # LangChain Runnable interface                                         #
    # ------------------------------------------------------------------ #
    def invoke(self, *args, **kwargs):
        try:
            return self._primary.invoke(*args, **kwargs)
        except Exception as exc:
            if self._secondary and _is_quota_error(exc):
                logger.warning(
                    "Primary LLM quota hit (%s). Falling back to %s.",
                    exc,
                    self._secondary_name,
                )
                return self._secondary.invoke(*args, **kwargs)
            raise

    async def ainvoke(self, *args, **kwargs):
        try:
            return await self._primary.ainvoke(*args, **kwargs)
        except Exception as exc:
            if self._secondary and _is_quota_error(exc):
                logger.warning(
                    "Primary LLM quota hit (%s). Falling back to %s.",
                    exc,
                    self._secondary_name,
                )
                return await self._secondary.ainvoke(*args, **kwargs)
            raise

    def stream(self, *args, **kwargs):
        try:
            yield from self._primary.stream(*args, **kwargs)
        except Exception as exc:
            if self._secondary and _is_quota_error(exc):
                logger.warning(
                    "Primary LLM quota hit (%s). Falling back to %s.",
                    exc,
                    self._secondary_name,
                )
                yield from self._secondary.stream(*args, **kwargs)
            else:
                raise

    # Delegate everything else (bind, with_config, etc.) to primary
    def __getattr__(self, name):
        return getattr(self._primary, name)


def get_llm():
    """
    Returns an LLM instance for the configured primary provider.
    If both API keys are present, wraps it in a _FallbackLLM so the app
    automatically retries with the other provider on quota errors.
    """
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "gemini":
        primary = _build_gemini()
        secondary = _build_groq() if settings.GROQ_API_KEY else None
        fallback_name = "groq"
    elif provider == "groq":
        primary = _build_groq()
        secondary = _build_gemini() if settings.GEMINI_API_KEY else None
        fallback_name = "gemini"
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Use 'gemini' or 'groq'."
        )

    if secondary:
        logger.info(
            "LLM: primary=%s, fallback=%s (auto-switches on quota errors)",
            provider,
            fallback_name,
        )
        return _FallbackLLM(primary, secondary, fallback_name)

    logger.info("LLM: using %s (no fallback configured)", provider)
    return primary


@lru_cache(maxsize=1)
def get_embeddings():
    """
    Returns an embedding instance compatible with LangChain / Chroma.
    Uses GoogleGenerativeAIEmbeddings if Gemini is configured.
    Returns None if using Chroma's built-in local ONNX MiniLM fallback.
    """
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "gemini" and settings.GEMINI_API_KEY:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )

    # Fallback to Chroma's built-in local embedding function (ONNX MiniLM)
    return None

