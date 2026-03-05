from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session_factory, engine
from app.models import Base

# Import models so Base.metadata knows about them
from app.models.incident import IncidentRow  # noqa: F401
from app.models.timeline_event import TimelineEventRow  # noqa: F401
from app.routes.incidents import router as incidents_router
from app.routes.ws import router as ws_router
from app.seed import seed_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        await seed_db(session)
    yield
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
app.include_router(ws_router)
