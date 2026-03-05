from app.schemas.agents import InvestigationResult, RootCauseResult


class RootCauseAgent:
    """Stub — will be wired to Amazon Nova / Bedrock."""

    async def run(self, investigation: InvestigationResult) -> RootCauseResult:
        raise NotImplementedError
