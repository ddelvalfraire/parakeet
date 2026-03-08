"""Agent runner — executes a LangChain tool-calling agent and returns tool calls."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10
LLM_RETRIES = 3
LLM_RETRY_BASE_DELAY = 2  # seconds

# Tools that produce final output (vs. exploratory tools like search/read).
# If the agent stops without calling any of these, it gets one nudge.
_OUTPUT_TOOLS = {
    "propose_remediation", "open_fix_pr", "report_exploration",
    "classify_alert",
    "report_log_findings", "report_affected_service", "report_impact_summary",
    "report_root_cause",
    "write_post_mortem",
}


@dataclass
class AgentConfig:
    """Lightweight agent definition: a name, system instruction, and tools."""

    name: str
    instruction: str
    tools: list[BaseTool] = field(default_factory=list)


def _tc_key(tc: dict[str, Any]) -> str:
    """Stable key for a tool call to detect repeated calls."""
    return f"{tc['name']}:{json.dumps(tc['args'], sort_keys=True)}"


async def run_agent(agent: AgentConfig, message: str) -> list[dict[str, Any]]:
    """Run agent with tool-calling loop, return all tool calls made.

    Returns a list of dicts: [{"name": "tool_name", "args": {...}}, ...]
    """
    llm_with_tools = settings.llm.bind_tools(agent.tools)

    messages = [
        SystemMessage(content=agent.instruction),
        HumanMessage(content=message),
    ]

    all_tool_calls: list[dict[str, Any]] = []
    seen_calls: set[str] = set()
    tools_by_name = {t.name: t for t in agent.tools}
    _nudged = False

    logger.info(
        "Agent %s starting — tools: %s",
        agent.name, [t.name for t in agent.tools],
    )

    for iteration in range(MAX_ITERATIONS):
        # Retry transient OpenRouter / provider errors with exponential backoff.
        for attempt in range(LLM_RETRIES):
            try:
                response: AIMessage = await llm_with_tools.ainvoke(messages)
                break
            except (APIError, APIConnectionError, APITimeoutError, RateLimitError) as exc:
                if attempt == LLM_RETRIES - 1:
                    raise
                delay = LLM_RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "Agent %s LLM call failed (attempt %d/%d): %s — retrying in %ds",
                    agent.name, attempt + 1, LLM_RETRIES, exc, delay,
                )
                await asyncio.sleep(delay)
        messages.append(response)

        if not response.tool_calls:
            text_preview = (response.content or "")[:200]
            logger.info(
                "Agent %s iter %d — no tool calls, text: %s",
                agent.name, iteration, text_preview,
            )
            # Nudge: if the agent has done work (read files, searched) but
            # never called any "output" tools, remind it to use its tools.
            called_names = {c["name"] for c in all_tool_calls}
            output_tools = called_names & _OUTPUT_TOOLS
            if all_tool_calls and not output_tools and not _nudged:
                _nudged = True
                logger.info("Agent %s nudged — has calls but no output tools", agent.name)
                messages.append(HumanMessage(
                    content=(
                        "You explored the code but did not call any output tools. "
                        "You MUST call your output tools (e.g. propose_remediation, "
                        "open_fix_pr, classify_alert, report_root_cause, etc.) with "
                        "your findings. Do not respond with only text."
                    ),
                ))
                continue
            break

        # Detect if all tool calls this round are duplicates of previous calls.
        # This prevents models (e.g. Nova) from looping on the same call.
        round_calls = [{"name": tc["name"], "args": tc["args"]} for tc in response.tool_calls]
        round_keys = {_tc_key(c) for c in round_calls}
        if round_keys.issubset(seen_calls):
            logger.info("Agent %s repeated tool calls — stopping loop", agent.name)
            break

        logger.info(
            "Agent %s iter %d — tool calls: %s",
            agent.name, iteration, [tc["name"] for tc in response.tool_calls],
        )

        for tc in response.tool_calls:
            call = {"name": tc["name"], "args": tc["args"]}
            all_tool_calls.append(call)
            seen_calls.add(_tc_key(call))

            tool = tools_by_name.get(tc["name"])
            if tool:
                result = await tool.ainvoke(tc["args"])
                call["result"] = result
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )
            else:
                logger.warning("Agent %s called unknown tool %s", agent.name, tc["name"])
                messages.append(
                    ToolMessage(content="Unknown tool", tool_call_id=tc["id"])
                )

    logger.info(
        "Agent %s finished — %d total tool calls: %s",
        agent.name, len(all_tool_calls), [c["name"] for c in all_tool_calls],
    )
    return all_tool_calls
