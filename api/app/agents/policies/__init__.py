"""Shared policy configs that feed into agent prompts."""

import functools
from pathlib import Path
from typing import Any

import yaml

_POLICIES_DIR = Path(__file__).parent


def load_severity_policy() -> dict[str, Any]:
    """Load the severity classification policy from YAML."""
    return yaml.safe_load((_POLICIES_DIR / "severity.yaml").read_text())


@functools.lru_cache(maxsize=1)
def severity_policy_as_prompt() -> str:
    """Render the severity policy as a text block for agent instructions."""
    policy = load_severity_policy()
    lines = ["## Severity Definitions\n"]
    for level, info in policy.items():
        lines.append(f"### {level} — {info['label']}")
        lines.append(info["description"].strip())
        lines.append("Examples:")
        for ex in info["examples"]:
            lines.append(f"  - {ex}")
        lines.append(f"Response time: {info['response_time']}")
        lines.append("")
    return "\n".join(lines)
