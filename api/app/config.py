from pathlib import Path

from pydantic_settings import BaseSettings

_API_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite+aiosqlite:///{_API_DIR / 'parakeet.db'}"
    cors_origins: list[str] = ["http://localhost:5173"]

    # LLM model used by ADK agents (swap to a Nova 2 model ID for prod)
    agent_model: str = "gemini-2.5-flash"

    model_config = {"env_prefix": "PARAKEET_"}


settings = Settings()
