import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session_factory, engine
from app.models import Base

# Import models so Base.metadata knows about them
from app.models.incident import IncidentRow  # noqa: F401
from app.models.timeline_event import TimelineEventRow  # noqa: F401
from app.routes.demo import router as demo_router
from app.routes.incidents import router as incidents_router
from app.routes.ws import router as ws_router
from app.seed import seed_db
from app.services.github_service import GitHubService


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        await seed_db(session)
    logger = logging.getLogger(__name__)
    if settings.mock_agents:
        logger.info("Mock agents ENABLED — no LLM calls will be made")
    else:
        logger.info("Using real ADK agents (model=%s)", settings.agent_model)

    # GitHub service for live demo remediation
    if settings.github_token and settings.demo_repo:
        _app.state.github = GitHubService(settings.github_token, settings.demo_repo)
        logger.info("GitHub integration ENABLED (repo=%s)", settings.demo_repo)
    else:
        _app.state.github = None
        logger.info(
            "GitHub integration disabled — set PARAKEET_GITHUB_TOKEN"
            " and PARAKEET_DEMO_REPO to enable"
        )

    yield

    if getattr(_app.state, "github", None):
        await _app.state.github.close()
    await engine.dispose()


app = FastAPI(title="Parakeet API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents_router)
app.include_router(demo_router)
app.include_router(ws_router)
