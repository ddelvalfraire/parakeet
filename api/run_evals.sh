#!/usr/bin/env bash
# Run eval sets for all agents (or a single agent if specified).
#
# Usage:
#   ./run_evals.sh              # run all agents
#   ./run_evals.sh triage       # run just triage
#   ./run_evals.sh triage root_cause  # run specific agents

set -euo pipefail

AGENTS_DIR="app/agents"

# All agents with eval sets
ALL_AGENTS=(triage investigation root_cause remediation retro)

# Use args if provided, otherwise run all
if [ $# -gt 0 ]; then
  AGENTS=("$@")
else
  AGENTS=("${ALL_AGENTS[@]}")
fi

PASS=0
FAIL=0

for agent in "${AGENTS[@]}"; do
  agent_dir="${AGENTS_DIR}/${agent}"
  eval_file=$(find "${agent_dir}" -name '*.evalset.json' 2>/dev/null | head -1)

  if [ -z "${eval_file}" ]; then
    echo "⚠ ${agent}: no eval set found, skipping"
    continue
  fi

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "▶ Running evals: ${agent}"
  echo "  Agent:    ${agent_dir}"
  echo "  Eval set: ${eval_file}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if poetry run adk eval "${agent_dir}" "${eval_file}"; then
    PASS=$((PASS + 1))
  else
    FAIL=$((FAIL + 1))
  fi

  echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Done. ${PASS} passed, ${FAIL} failed out of ${#AGENTS[@]} agents."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ "${FAIL}" -eq 0 ]
