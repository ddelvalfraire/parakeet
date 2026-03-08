# Parakeet

AI-powered incident response system that automatically triages, investigates, diagnoses, and remediates production incidents using Amazon Nova agents.

**Live demo:** [parakeet.daves-wave.dev](https://parakeet.daves-wave.dev)

## What It Does

Parakeet chains five specialized AI agents into an end-to-end incident response pipeline:

1. **Triage** — classifies alerts by severity (P1-P4), category, and tags
2. **Investigation** — analyzes logs, maps blast radius, estimates user impact
3. **Root Cause Analysis** — identifies probable cause with confidence scoring, checks for similar past incidents
4. **Remediation** — proposes ranked fix options (rollback, hotfix, mitigation) with risk assessment; optionally opens a GitHub PR with the fix
5. **Retrospective** — generates a blameless post-mortem report after resolution

The pipeline runs asynchronously with real-time WebSocket updates, so operators see each stage complete live in the browser. A human-in-the-loop approval step gates remediation before any action is taken.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI, SQLAlchemy (async), SQLite |
| **AI Agents** | LangChain, OpenAI SDK, Amazon Nova 2 Lite via OpenRouter |
| **Similarity Search** | Sentence Transformers (all-MiniLM-L6-v2), cosine similarity |
| **Frontend** | React 19, React Router 7, Tailwind CSS 4, shadcn/ui, Recharts |
| **Real-time** | WebSocket with auto-reconnect |
| **Deployment** | Docker Compose, nginx reverse proxy, Coolify |

## Architecture

```
Browser (React SPA)
  │
  ├── REST API ──► FastAPI ──► Agent Pipeline
  │                   │            │
  │                   │            ├── Triage Agent
  │                   │            ├── Investigation Agent
  │                   │            ├── Root Cause Agent
  │                   │            ├── Remediation Agent (+ GitHub PR)
  │                   │            └── Retro Agent
  │                   │
  └── WebSocket ◄────┘ (live stage updates)
                      │
                      ├── SQLite (incidents, timeline, embeddings)
                      └── GitHub API (demo PR creation)
```

## Demo System

Three pre-baked bug scenarios from an [Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo) fork:

| Scenario | Service | Language | Bug |
|----------|---------|----------|-----|
| Flat-rate shipping | shippingservice | Go | Hardcoded 0 passed to quote calculator |
| Currency conversion | currencyservice | Node.js | Missing validation causes NaN propagation |
| Recommendation crash | recommendationservice | Python | `random.sample` exceeds pool size |

Each demo launches the full pipeline, and if GitHub integration is configured, the remediation agent reads the repo, finds the bug, and opens a PR with a fix.

## Running Locally

### Prerequisites
- Python 3.12+, Node 22+, Poetry
- OpenRouter API key (or use mock mode)

### Backend
```bash
cd api
cp .env.example .env          # add your OPENROUTER_API_KEY
poetry install
poetry run uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Mock Mode (no LLM costs)
Set `PARAKEET_MOCK_AGENTS=true` in your `.env`. The mock pipeline returns deterministic, context-aware responses with realistic delays.

### Docker Compose
```bash
docker compose up --build
```

## Project Structure

```
api/
  app/
    agents/           # 5 LangChain agents with structured tools
    models/           # SQLAlchemy ORM (incidents, timeline, embeddings)
    routes/           # REST + WebSocket endpoints
    schemas/          # Pydantic request/response models
    services/         # Pipeline orchestration, GitHub, similarity search
  fixtures/           # Demo scenarios + seed data
  Dockerfile

frontend/
  src/
    pages/            # Landing, Dashboard, IncidentDetail, Retrospective
    components/       # Incident cards, timeline, demo launcher
    hooks/            # WebSocket, polling
    api/              # HTTP + mock clients
    lib/              # Design tokens, utilities
  Dockerfile
  nginx.conf

docker-compose.yml
```

## Key Design Decisions

- **Agent-per-stage architecture** — each agent has a single responsibility with typed tool outputs, making the pipeline debuggable and independently testable
- **Event sourcing** — every agent decision is stored as an immutable timeline event, creating a full audit trail
- **Mock/real duality** — the pipeline is swappable between mock (deterministic) and real (LLM) agents via a single env var, enabling frontend development without token spend
- **Embedding-based similarity** — resolved incidents are indexed by semantic embeddings so the root cause agent can reference similar past incidents
- **Human-in-the-loop** — remediation requires explicit operator approval before any action is taken
