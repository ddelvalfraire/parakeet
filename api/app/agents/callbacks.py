"""Shared ADK agent callbacks."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from google.adk.agents import CallbackContext
    from google.adk.models.llm_request import LlmRequest
    from google.adk.models.llm_response import LlmResponse

logger = logging.getLogger(__name__)


async def patch_empty_tool_descriptions(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Ensure all tool declarations have non-empty descriptions.

    Amazon Bedrock (behind OpenRouter Nova models) requires all tool
    descriptions to be non-empty.  ADK may add internal tools whose
    descriptions are empty strings, causing Bedrock to return a 400.
    This callback patches them before the request is sent.
    """
    if llm_request.config and llm_request.config.tools:
        for tool in llm_request.config.tools:
            if not tool.function_declarations:
                continue
            for decl in tool.function_declarations:
                if not decl.description:
                    decl.description = f"Invoke the {decl.name} tool."
                    logger.debug(
                        "Patched empty description for tool %r", decl.name
                    )
    return None
