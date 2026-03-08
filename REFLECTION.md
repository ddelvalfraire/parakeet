# Reflection

## Activity Description

Parakeet is an AI-powered incident response platform built for the Amazon Nova hackathon. It helps engineering teams solve production incidents faster by automating the triage, investigation, root cause analysis, and remediation stages. An alert comes in, AI agents process it through a structured pipeline, and the on-call engineer reviews and approves the proposed fix. The goal is to cut incident response time, not replace the human in the loop.

## Technical Decisions

I split the pipeline into five independent agents instead of one monolithic prompt because each stage has a different job and different output schema. This made it easier to debug when a stage produced bad results since I could test and iterate on each agent in isolation. Each agent uses typed tool functions as its output contract, which was a deliberate choice over free-form JSON since downstream stages depend on the structure being correct.

I chose FastAPI over something like Flask because the pipeline needs to run asynchronously in a background task while WebSockets push progress to the browser. Synchronous frameworks would have blocked on LLM calls. For the database, I went with SQLite because it's zero-config and good enough for a hackathon, but in hindsight Postgres would have been better since SQLite doesn't handle concurrent writes from multiple pipeline runs.

I initially built the agent layer on Google's ADK with LiteLLM as a translation layer to OpenRouter. That introduced too many abstraction layers and caused hard-to-debug serialization issues between ADK, LiteLLM, and Amazon Bedrock's tool schema requirements. I stripped both out and rebuilt on LangChain with the OpenAI SDK hitting OpenRouter directly. Fewer moving parts, and the tool calling just worked.

I also built a mock pipeline mode that returns canned responses without hitting the LLM, which let me build the entire frontend and API integration without burning credits.

For deployment I used Docker Compose with an nginx reverse proxy on Coolify. I used multi-stage Docker builds and CPU-only PyTorch to keep the image size manageable since the full PyTorch package added 2GB for a feature that only needed CPU inference.

## Contributions

Solo project. I handled the architecture, backend API, agent pipeline, prompt engineering, frontend, demo scenarios, Docker setup, and deployment.

## Quality Assessment

The pipeline architecture is solid. Each agent stage produces structured output via tool calling, and every decision is stored as a timeline event so you can trace exactly what happened. The mock pipeline was a good investment for fast frontend iteration.

The main gap was deployment reliability. My initial choice of ADK + LiteLLM created integration issues that only surfaced in the container environment, not locally. Migrating to LangChain + OpenAI SDK fixed it but cost time I could have spent on features. Next time I would test the full LLM integration end-to-end in the container early instead of building out features first. I would also swap SQLite for Postgres for better concurrency and add retry logic around the LLM calls.
