from app.schemas.agents import PostMortem
from app.schemas.incident import Incident


class RetroAgent:
    """Stub — will be wired to Amazon Nova / Bedrock."""

    async def run(self, incident: Incident) -> PostMortem:
        raise NotImplementedError
