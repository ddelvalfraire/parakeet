from app.schemas.agents import InvestigationResult, TriageResult


class InvestigationAgent:
    """Stub — will be wired to Amazon Nova / Bedrock."""

    async def run(self, triage: TriageResult) -> InvestigationResult:
        raise NotImplementedError
