from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./parakeet.db"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_prefix": "PARAKEET_"}


settings = Settings()
