# Reflection

## Activity Description

I wanted to build something that tackled a real problem I've seen in production engineering: incident response is slow, repetitive, and stressful. When an alert fires at 3am, you're digging through logs, trying to figure out what broke, and scrambling to fix it. I thought it would be interesting to see how far AI agents could go in automating that workflow.

So I built Parakeet, an incident response system where AI agents handle triage, investigation, root cause analysis, and remediation automatically. The idea is that an alert comes in, agents work through the problem step by step, and then a human approves the fix before anything actually gets deployed. I gave myself about 12 hours to build and deploy it end to end.

## Technical Decisions

I went with Google's Agent Development Kit because it lets you define agents with structured tool calling. Instead of hoping the LLM returns the right JSON, each agent has typed functions like `classify_alert()` or `report_root_cause()` that force it into a schema. This turned out to be really important because the agents feed into each other, and if one stage returns garbage, the whole pipeline falls apart.

For the backend I used FastAPI since the pipeline runs asynchronously in background tasks while WebSockets push updates to the browser in real time. I picked Amazon Nova 2 Lite as the LLM through OpenRouter, which gave me a single API to work with instead of dealing with AWS Bedrock directly.

On the frontend, React with shadcn/ui got me to a usable interface fast. I also built a mock pipeline mode that returns deterministic responses without calling any LLM, which saved me a lot of money during frontend development.

Deployment was honestly the hardest part. Getting Docker Compose working on Coolify meant debugging SQLite file permissions, CORS parsing quirks with pydantic-settings, nginx WebSocket proxying, and figuring out that PyTorch was adding 2GB to my Docker image when I only needed the CPU version.

## Contributions

I worked on this alone. Architecture, backend, frontend, agent prompts, demo scenarios, Docker setup, and deployment were all me. The repo has 129 commits across 26 pull requests.

## Quality Assessment

I think the core architecture is solid. Breaking the pipeline into one agent per stage with event sourcing means you can see exactly what each agent decided and why. The mock pipeline was probably my best call since it let me iterate on the UI without burning through API credits.

Where I fell short was deployment stability. I spent a lot of time fighting OpenRouter connection issues and LiteLLM configuration quirks that I could have avoided with better upfront research. If I did this again, I'd set up a simple end-to-end test that calls the real LLM API early on instead of waiting until deployment to discover integration problems. I'd also want to add retry logic for transient API failures and swap SQLite for Postgres since SQLite doesn't handle concurrent writes well.
