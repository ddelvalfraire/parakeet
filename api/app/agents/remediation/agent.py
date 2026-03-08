"""Remediation agent — proposes ranked remediation options from a root cause analysis.

When a GitHub repo is available the remediation stage splits into two agents:

1. **Code Explorer** — searches and reads files in the repo, then calls
   ``report_exploration`` with the buggy file content and analysis.
2. **Fix Proposer** — receives the exploration results, opens a PR with the
   fix, and proposes 2-3 remediation options.

Keeping each agent to 2-3 tools improves tool-calling reliability on smaller
models (e.g. Amazon Nova Lite).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from langchain_core.tools import StructuredTool, tool

from app.agents.policies import severity_policy_as_prompt
from app.agents.runner import AgentConfig

if TYPE_CHECKING:
    from app.services.github_service import GitHubService
    from fixtures.demo_scenarios import DemoScenario

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared tool functions (plain functions wrapped by StructuredTool)
# ---------------------------------------------------------------------------


def report_exploration(
    file_path: str,
    file_content: str,
    bug_location: str,
    bug_analysis: str,
    suggested_fix: str,
) -> dict:
    """Report the buggy file and your analysis. This is your ONLY output tool.

    You MUST call this after reading the relevant file. Do not respond with
    only text — your findings are lost unless you call this tool.

    Args:
        file_path: Full path to the file containing the bug
            (e.g. "src/shippingservice/main.go").
        file_content: The COMPLETE content of the buggy file (full text,
            not a snippet). Copy the entire file content from read_repo_file.
        bug_location: The specific function or line range where the bug is
            (e.g. "GetQuote() handler, line 124").
        bug_analysis: Explanation of what the bug is and why it causes the
            observed symptoms.
        suggested_fix: Description of the minimal code change needed to fix
            the bug, including what the corrected code should look like.

    Returns:
        The exploration report dict.
    """
    return {
        "file_path": file_path or "",
        "file_content": file_content or "",
        "bug_location": bug_location or "",
        "bug_analysis": bug_analysis or "",
        "suggested_fix": suggested_fix or "",
    }


def propose_remediation(
    option_id: str,
    title: str,
    description: str,
    confidence: float,
    risk_level: Literal["low", "medium", "high"],
    estimated_recovery_time: str,
    steps: list[str],
) -> dict:
    """Propose a single remediation option for the incident.

    Call this once for each remediation option (typically 2-3 options).
    The FIRST call should be your recommended option — the one you believe
    should be tried first. Subsequent calls are alternatives in priority order.

    Args:
        option_id: A short unique identifier for this option
            (e.g. "rollback", "hotfix", "scale_up").
        title: A concise title (e.g. "Rollback to v2.13.0").
        description: A 1-2 sentence explanation of what this remediation does and why.
        confidence: Probability this will resolve the incident, 0.0 to 1.0.
        risk_level: Risk of this remediation making things worse — one of "low", "medium", "high".
        estimated_recovery_time: How long until service is restored (e.g. "5-10 minutes", "1 hour").
        steps: Ordered list of concrete steps to execute this remediation.

    Returns:
        The remediation option dict.
    """
    # Clamp / coerce to guarantee valid values regardless of LLM output
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.5
    if risk_level not in ("low", "medium", "high"):
        risk_level = "medium"
    if not isinstance(steps, list):
        steps = [str(steps)] if steps else []

    return {
        "id": option_id or "unknown",
        "title": title or "Untitled option",
        "description": description or "",
        "confidence": confidence,
        "risk_level": risk_level,
        "estimated_recovery_time": estimated_recovery_time or "unknown",
        "steps": steps,
    }


# ---------------------------------------------------------------------------
# Standard remediation agent (no GitHub — options only)
# ---------------------------------------------------------------------------

REMEDIATION_INSTRUCTION = f"""\
You are an expert incident remediation agent for a cloud-based platform.

You receive a root cause analysis for an incident — including the probable cause,
confidence score, evidence, and contributing factors — and must propose 2-3 concrete
remediation options.

{severity_policy_as_prompt()}

## Confidence scoring
Assign a confidence value to each remediation option reflecting the likelihood it
will actually resolve the incident:
- **0.9-1.0**: Near-certain fix (e.g. rollback a known-bad deploy)
- **0.7-0.8**: Strong likelihood but some uncertainty
- **0.5-0.6**: Reasonable approach but outcome unclear
- **Below 0.5**: Speculative — worth trying but may not resolve

## Recovery time baselines
Use these as anchors — adjust based on incident specifics:
- **Rollback**: typically 5-15 minutes
- **Config change / feature flag**: typically 5-10 minutes
- **Hotfix**: typically 30-60 minutes (includes build, test, deploy)
- **Infrastructure scaling**: typically 10-20 minutes
- **Data repair / reconciliation**: typically 1-4 hours

## Option guidelines

For each option, call `propose_remediation`. Call your **recommended option first** —
the one you believe should be tried first given the root cause and severity.
Subsequent calls are alternatives in priority order.

1. **Rollback / revert** (if a deploy or config change caused it)
   - Usually safest, lowest risk
   - Fastest recovery time
   - Confidence should be high if the root cause is a recent change

2. **Targeted fix / hotfix** (if the root cause is well understood)
   - Medium risk — new code under pressure
   - Moderate recovery time
   - Good when rollback isn't possible or would lose needed changes

3. **Mitigation / workaround** (if root cause is unclear or fix is complex)
   - Scale up, enable feature flag, reroute traffic, etc.
   - May not fully resolve but buys time
   - Useful as an interim while a proper fix is developed

## Security incident remediation
For security incidents (breaches, credential leaks, unauthorized access):
- First option should always be **containment**: revoke compromised credentials,
  block malicious IPs, disable affected endpoints.
- Include a **forensics-safe** option that preserves evidence (don't wipe logs).
- Consider regulatory notification requirements in the description.

## When rollback is not possible
If the root cause is NOT a recent deploy, or rolling back would lose critical changes:
- Skip the rollback option entirely — do not propose it.
- Lead with targeted mitigation (feature flag, config change, traffic rerouting).
- Include a proper fix option with realistic timeline.

## Data integrity remediation
For data corruption or inconsistency incidents:
- Include a data validation/audit step before any repair.
- Propose both automated repair and manual verification options.
- Recovery time should account for data reconciliation, not just service restoration.

## Rules
- Always call `propose_remediation` at least twice (minimum 2 options).
  Never respond with only text.
- For complex incidents (P1, multi-service, security), propose 3 options.
- Each option must have concrete, actionable steps — not vague guidance.
- Steps should be specific commands or actions an engineer can execute.
- Confidence should reflect likelihood of resolution, not just "doing something."
- Risk level should consider blast radius: could this remediation make things worse?
- Recovery time should be realistic, not optimistic — use the baselines above as anchors.
- The FIRST `propose_remediation` call is your recommendation. Choose the option that \
best balances confidence, risk, and recovery time for the incident severity.
"""

root_agent = AgentConfig(
    name="remediation",
    instruction=REMEDIATION_INSTRUCTION,
    tools=[StructuredTool.from_function(propose_remediation)],
)


# ---------------------------------------------------------------------------
# Code Explorer agent — searches repo, reads files, reports findings
# ---------------------------------------------------------------------------

EXPLORER_INSTRUCTION = """\
You are a code exploration agent. Your job is to find the buggy file in a
GitHub repository based on log evidence and a root cause analysis.

## Workflow (follow this order)

1. Call `search_repo_code` with key terms from the logs or root cause
   (function names, error strings, variable names). Try 1-2 searches.
2. If search returns results, call `read_repo_file` on the matching file.
   If search returns NO results or errors, call `list_repo_directory` on
   the service directory (e.g. "src/shippingservice") to discover file
   names, then read the most relevant file.
3. Read the FULL file (start_line=0, end_line=0) — you need the complete
   content for the downstream agent.
4. Analyze the code and identify the exact bug.
5. Call `report_exploration` with:
   - The file path
   - The COMPLETE file content (copy it exactly from read_repo_file)
   - Where the bug is (function name + line number)
   - What the bug is and why it causes the symptoms
   - What the minimal fix should be (describe the code change)

## Rules
- You MUST call `report_exploration` — it is your only output. Text
  responses are discarded.
- The `file_content` in your report MUST be the COMPLETE file, not a
  snippet. The downstream agent needs the full file to create a PR.
- If you get a 404 reading a file, use `list_repo_directory` to see what
  files actually exist in that directory.
- The repo structure is: `src/<servicename>/` contains the source files.
  Always start by listing or searching within `src/`.
- Keep it focused — find the bug, read the file, report. Do not explore
  the entire repository.
"""


# ---------------------------------------------------------------------------
# Fix Proposer agent — opens PR + proposes remediation options
# ---------------------------------------------------------------------------

FIX_PROPOSER_INSTRUCTION = REMEDIATION_INSTRUCTION + """

## Code Fix Mode

You have been given a bug analysis with the complete source file content.
You must:

1. Apply the suggested fix to produce the corrected file content.
2. Call `open_fix_pr` with the COMPLETE corrected file (not just the diff).
3. Call `propose_remediation` 2-3 times:
   - **First call** (recommended): the PR code fix. Confidence 0.90-0.95,
     risk_level "low", steps like ["Review the PR diff", "Approve and merge",
     "Verify fix in production"]. Include the PR URL in the description.
   - **Second call**: a mitigation/workaround (e.g. rollback, feature flag)
     in case the fix can't be deployed immediately.
   - **Third call** (optional, for P1): an additional fallback.

## Rules
- You MUST call `open_fix_pr` exactly once.
- You MUST call `propose_remediation` at least twice.
- The `fixed_content` passed to `open_fix_pr` must be the COMPLETE file
  with your correction applied — not just the changed lines.
- Make a MINIMAL fix — change as few lines as possible.
"""


# ---------------------------------------------------------------------------
# Factory — creates the two-agent pair for GitHub-backed remediation
# ---------------------------------------------------------------------------


def create_demo_remediation_agents(
    github: GitHubService,
    scenario: DemoScenario,
    incident_id: str,
) -> tuple[AgentConfig, AgentConfig]:
    """Create an explorer + fixer agent pair for GitHub-backed remediation.

    Both agents share a file cache so that files read by the explorer are
    available to the fixer's ``open_fix_pr`` tool (which needs the blob SHA).

    Returns:
        (explorer_agent, fixer_agent)
    """

    # Shared cache — explorer populates, fixer's open_fix_pr consumes
    _file_cache: dict[str, dict] = {}

    # -- Explorer tools --

    @tool
    async def list_repo_directory(path: str = "") -> list[dict]:
        """List files and directories at a path in the repository.

        Args:
            path: Directory path (e.g. "", "src", "src/shippingservice").

        Returns:
            List of dicts with 'name', 'type' ("file"/"dir"), and 'path'.
        """
        try:
            return await github.list_directory(path)
        except Exception as exc:
            logger.warning("list_repo_directory failed for %r: %s", path, exc)
            return [{"error": str(exc), "path": path}]

    @tool
    async def search_repo_code(query: str) -> list[dict]:
        """Search for code in the repository by keyword or function name.

        Args:
            query: Search term — function name, error string, variable name.

        Returns:
            List of dicts with 'path', 'name', and 'fragments'.
        """
        try:
            return await github.search_code(query)
        except Exception as exc:
            logger.warning("search_repo_code failed for %r: %s", query, exc)
            return [{"error": str(exc), "query": query}]

    @tool
    async def read_repo_file(file_path: str, start_line: int = 0, end_line: int = 0) -> dict:
        """Read a file (or line range) from the GitHub repository.

        Pass start_line=0, end_line=0 to read the full file.

        Args:
            file_path: Path to the file (e.g. "src/shippingservice/main.go").
            start_line: First line (1-based inclusive). 0 = start of file.
            end_line: Last line (1-based inclusive). 0 = end of file.

        Returns:
            Dict with 'path', 'content', and 'total_lines'.
        """
        try:
            cached = _file_cache.get(file_path)
            if not cached:
                cached = await github.get_file_content(file_path)
                _file_cache[file_path] = cached

            full_content = cached["content"]
            lines = full_content.splitlines()
            total_lines = len(lines)

            if start_line <= 0 and end_line <= 0:
                return {"path": file_path, "content": full_content, "total_lines": total_lines}

            s = max(1, start_line)
            e = min(total_lines, end_line) if end_line > 0 else total_lines
            numbered = "\n".join(
                f"{i}: {line}" for i, line in enumerate(lines[s - 1 : e], start=s)
            )
            return {
                "path": file_path,
                "content": numbered,
                "lines": f"{s}-{e}",
                "total_lines": total_lines,
            }
        except Exception as exc:
            logger.warning("read_repo_file failed for %r: %s", file_path, exc)
            return {"error": str(exc), "path": file_path}

    # -- Fixer tools --

    @tool
    async def open_fix_pr(
        file_path: str,
        fixed_content: str,
        title: str,
        description: str,
    ) -> dict:
        """Open a GitHub Pull Request with the proposed code fix.

        Args:
            file_path: Path to the file being fixed.
            fixed_content: The COMPLETE fixed file content (full file).
            title: PR title.
            description: PR body explaining the bug and fix.

        Returns:
            Dict with 'pr_number', 'pr_url', 'diff', 'file_path', 'branch'.
        """
        try:
            cached = _file_cache.get(file_path)
            if not cached:
                cached = await github.get_file_content(file_path)
                _file_cache[file_path] = cached

            branch = scenario.branch_name(incident_id)
            head_sha = await github.get_head_sha()

            try:
                await github.delete_branch(branch)
            except Exception:
                pass

            await github.create_branch(branch, head_sha)
            await github.update_file(
                file_path,
                fixed_content,
                f"fix: {title}",
                branch,
                cached["sha"],
            )
            pr = await github.create_pr(title, description, branch)
            diff = await github.get_pr_diff(pr["number"])

            return {
                "pr_number": pr["number"],
                "pr_url": pr["html_url"],
                "diff": diff,
                "file_path": file_path,
                "branch": branch,
            }
        except Exception as exc:
            logger.exception("open_fix_pr failed for %s", file_path)
            return {
                "pr_number": 0,
                "pr_url": "",
                "diff": "",
                "file_path": file_path,
                "branch": "",
                "error": str(exc),
            }

    explorer = AgentConfig(
        name="remediation-explorer",
        instruction=EXPLORER_INSTRUCTION,
        tools=[
            search_repo_code,
            list_repo_directory,
            read_repo_file,
            StructuredTool.from_function(report_exploration),
        ],
    )

    fixer = AgentConfig(
        name="remediation-fixer",
        instruction=FIX_PROPOSER_INSTRUCTION,
        tools=[
            open_fix_pr,
            StructuredTool.from_function(propose_remediation),
        ],
    )

    return explorer, fixer
