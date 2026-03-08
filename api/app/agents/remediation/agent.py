"""Remediation agent — proposes ranked remediation options from a root cause analysis."""

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
# Demo mode — agent factory with GitHub-backed tools
# ---------------------------------------------------------------------------

DEMO_INSTRUCTION_ADDON = """

## Live Code Fix Mode

You have access to a real GitHub repository containing the source code for
Google's Online Boutique microservices application. Based on the root cause
analysis and log evidence provided, you must **find** the buggy file and open a
Pull Request with the fix.

### Workflow

1. **Search first** — call `search_repo_code` with key terms from the log
   evidence or root cause (function names, error strings, variable names).
   This returns matching file paths and code fragments so you can pinpoint
   the relevant file and function without reading every file.
2. **Read the targeted range** — once you know the file and approximate
   location, call `read_repo_file` with `start_line` / `end_line` to inspect
   just the function or block that contains the bug. This saves tokens and
   focuses your analysis.
3. **Explore if needed** — if search returns no results or you need to browse
   the directory structure, fall back to `list_repo_directory` starting at
   `src/` to discover service directories, then drill into the relevant one.
4. **Read the full file** — before opening the PR you need the complete file
   content. Call `read_repo_file` with no line range (start_line=0, end_line=0)
   on the file you want to fix. This fetches and caches the full text.
5. Analyze the code and identify the exact bug that matches the log evidence.
6. Determine the **minimal** fix — change as few lines as possible.
7. Call `open_fix_pr` with the complete corrected file content, a clear title,
   and a description explaining the bug and fix.
8. Call `propose_remediation` **2-3 times** as you normally would:
   - **First call** (recommended): the PR code fix. Confidence 0.90-0.95,
     risk_level "low", steps like ["Review the PR diff", "Approve and merge",
     "Verify fix in production"]. Include the PR URL in the description.
   - **Second call**: a mitigation/workaround option (e.g. feature flag,
     traffic reroute, rollback to previous version) in case the fix can't be
     deployed immediately. Use the standard confidence/risk/recovery guidelines.
   - **Third call** (optional, for P1): an additional fallback option.

### Tool usage tips
- **`search_repo_code`** is cheap and fast — always try it first.
  Good queries: function names (`CreateQuoteFromCount`), error strings
  (`getRate`), log patterns (`random.sample`).
- **`read_repo_file` with a range** — use when search tells you the file and
  you want to inspect ~20-50 lines around the match. Pass `start_line` and
  `end_line` (1-based, inclusive).
- **`read_repo_file` without a range** — use once before `open_fix_pr` to
  get the complete file. The cached content is reused automatically.
- **`list_repo_directory`** — use as a fallback when search doesn't help
  or you need to see the repo layout.

### Important
- You MUST search or explore and read files before opening a PR — never guess.
- You MUST call both `open_fix_pr` and `propose_remediation` (at least twice).
- Include the PR URL in the first remediation option's description.
- The `fixed_content` passed to `open_fix_pr` must be the COMPLETE file with
  your correction applied, not just the changed lines.
"""


def create_demo_remediation_agent(
    github: GitHubService,
    scenario: DemoScenario,
    incident_id: str,
) -> AgentConfig:
    """Create a remediation agent wired to a live GitHub repo for a demo scenario."""

    # Stash file metadata from read_repo_file for use in open_fix_pr
    _file_cache: dict[str, dict] = {}

    @tool
    async def list_repo_directory(path: str = "") -> list[dict]:
        """List files and directories at a path in the demo GitHub repository.

        Use this to explore the repo structure and locate source files.
        Start with the root or "src/" to discover service directories,
        then drill into specific services.

        Args:
            path: Directory path in the repository (e.g. "", "src",
                "src/shippingservice"). Empty string lists the repo root.

        Returns:
            List of dicts, each with 'name', 'type' ("file" or "dir"),
            and 'path' (full path from repo root).
        """
        return await github.list_directory(path)

    @tool
    async def search_repo_code(query: str) -> list[dict]:
        """Search for code in the repository by keyword, function name, or error string.

        Use this FIRST to locate relevant files and symbols before reading files.
        Returns file paths and text fragments showing matches in context.

        Args:
            query: Search term — function name, error string, variable name, etc.
                Examples: "CreateQuoteFromCount", "getRate", "random.sample".

        Returns:
            List of dicts, each with 'path' (file path), 'name' (filename),
            and 'fragments' (list of code snippets showing the match in context).
        """
        return await github.search_code(query)

    @tool
    async def read_repo_file(file_path: str, start_line: int = 0, end_line: int = 0) -> dict:
        """Read a file (or a line range) from the demo GitHub repository.

        When start_line and end_line are both 0, returns the full file.
        Otherwise returns only the requested line range with line numbers.

        Tip: Use `search_repo_code` first to find the file and approximate
        location, then read a targeted range to inspect specific functions.

        Args:
            file_path: Path to the file in the repository
                (e.g. "src/shippingservice/main.go").
            start_line: First line to return (1-based, inclusive). 0 = start of file.
            end_line: Last line to return (1-based, inclusive). 0 = end of file.

        Returns:
            Dict with 'path', 'content', and 'total_lines'.
            When a range is requested, 'content' is prefixed with line numbers.
        """
        # Always fetch and cache the full file (needed for open_fix_pr later)
        cached = _file_cache.get(file_path)
        if not cached:
            cached = await github.get_file_content(file_path)
            _file_cache[file_path] = cached

        full_content = cached["content"]
        lines = full_content.splitlines()
        total_lines = len(lines)

        # Full file requested
        if start_line <= 0 and end_line <= 0:
            return {"path": file_path, "content": full_content, "total_lines": total_lines}

        # Line range requested — clamp and return with line numbers
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

    @tool
    async def open_fix_pr(
        file_path: str,
        fixed_content: str,
        title: str,
        description: str,
    ) -> dict:
        """Open a GitHub Pull Request with the proposed code fix.

        Args:
            file_path: Path to the file being fixed (must have been read first).
            fixed_content: The COMPLETE fixed file content (full file, not just the diff).
            title: PR title (e.g. "Fix: Pass actual cart size to CreateQuoteFromCount").
            description: PR body explaining the bug, evidence, and fix.

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

    return AgentConfig(
        name="remediation-demo",
        instruction=REMEDIATION_INSTRUCTION + DEMO_INSTRUCTION_ADDON,
        tools=[
            search_repo_code,
            list_repo_directory,
            read_repo_file,
            open_fix_pr,
            StructuredTool.from_function(propose_remediation),
        ],
    )
