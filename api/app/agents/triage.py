from app.schemas.agents import TriageResult
from app.schemas.alert import Alert


class TriageAgent:
    """Stub — will be wired to Amazon Nova / Bedrock."""

    async def run(self, alert: Alert) -> TriageResult:
        raise NotImplementedError
