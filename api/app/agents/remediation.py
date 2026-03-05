from app.schemas.agents import RemediationResult, RootCauseResult


class RemediationAgent:
    """Stub — will be wired to Amazon Nova / Bedrock."""

    async def run(self, root_cause: RootCauseResult) -> RemediationResult:
        raise NotImplementedError
