from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.config import get_settings, get_engine
from database.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    logger = setup_logging(settings.debug)
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug}")
    yield
    # Shutdown
    logger.info("Shutting down...")


settings = get_settings()

app = FastAPI(
    title="openMinistry API",
    description="Public archive of Kerala minister statements",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes.auth import router as auth_router
app.include_router(auth_router)

from api.routes.sources import router as sources_router
app.include_router(sources_router)

from api.routes.tasks import router as tasks_router
app.include_router(tasks_router)

from api.routes.ministers import router as ministers_router
app.include_router(ministers_router)


@app.get("/")
async def root():
    return {
        "project": "openMinistry",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Used by Docker and monitoring to verify the service is alive."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}