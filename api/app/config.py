from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings

_API_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite+aiosqlite:///{_API_DIR / 'parakeet.db'}"
    cors_origins: list[str] = ["http://localhost:5173"]

    # LLM model used by ADK agents (via LiteLLM + OpenRouter)
    agent_model: str = "openrouter/amazon/nova-2-lite-v1"

    @cached_property
    def adk_model(self):
        """Wrap agent_model in LiteLlm for ADK compatibility."""
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm(model=self.agent_model)

    # Use mock agents (deterministic, no LLM calls) for frontend development
    mock_agents: bool = False

    # Simulate an agent failure at a specific stage (mock pipeline only).
    # Set to "triage", "investigation", "root_cause", or "remediation".
    mock_error_stage: str = ""

    # Similar-incidents embedding search
    embedding_model: str = "all-MiniLM-L6-v2"
    similarity_min_score: float = 0.3
    similarity_max_results: int = 5

    # GitHub integration for live demo remediation
    github_token: str = ""
    demo_repo: str = ""           # owner/repo for the Online Boutique fork
    demo_base_sha: str = ""       # commit SHA of the buggy main branch (for reset)

    model_config = {"env_prefix": "PARAKEET_", "env_file": _API_DIR / ".env", "extra": "ignore"}


settings = Settings()
