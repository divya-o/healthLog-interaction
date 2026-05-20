from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine

from app.models import hcp, interaction, followUp  # noqa: F401


from app.routes.hcps import router as hcps_router
from app.routes.interactions import router as interactions_router
from app.routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables, clean up on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="HCP CRM",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcps_router,  prefix="/api/hcps",   tags=["HCPs"])
app.include_router(interactions_router, prefix="/api/interactions", tags=["Interactions"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])


@app.get("/health", tags=["System"])
async def health():
    """check to confirm the server is running"""
    return {"status": "ok"}