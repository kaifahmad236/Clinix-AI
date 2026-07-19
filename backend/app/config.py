from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str = "insecure-dev-key-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite:///./clinixai.db"

    LLM_PROVIDER: str = "gemini"  # "gemini" or "groq"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # Comma-separated list of allowed CORS origins (e.g. your production
    # frontend domain). Falls back to localhost dev origins if unset.
    FRONTEND_ORIGINS: str = ""


settings = Settings()
