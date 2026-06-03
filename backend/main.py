from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database.config import get_settings, get_engine
from database.logging_config import setup_logging
from api.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger = setup_logging(settings.debug)
    logger.info(f"Starting {settings.app_name}")
    yield
    logger.info("Shutting down...")


settings = get_settings()

app = FastAPI(
    title="openMinistry API",
    description="""
## openMinistry Public API

A public API for accessing verified statements made by Kerala
ministers and MLAs.

### Authentication
Public endpoints require no authentication.
Admin/moderation endpoints require a Bearer token.

### Rate Limiting
- Public endpoints: 60 requests per minute
- Search endpoints: 30 requests per minute

### Data
All statements are verified by human moderators before publication.
    """,
    version="1.0.0",
    contact={
        "name": "openMinistry",
        "url": "https://openministry.live",
    },
    license_info={
        "name": "AGPL-3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0.html",
    },
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://openministry.live"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
from api.routes.auth import router as auth_router
from api.routes.sources import router as sources_router
from api.routes.ministers import router as ministers_router
from api.routes.statements import router as statements_router
from api.routes.search import router as search_router
from api.routes.tasks import router as tasks_router
from api.routes.moderation import router as moderation_router
from api.routes.public import router as public_router
from api.routes.queue import router as queue_router

app.include_router(auth_router)
app.include_router(sources_router)
app.include_router(ministers_router)
app.include_router(statements_router)
app.include_router(search_router)
app.include_router(tasks_router)
app.include_router(moderation_router)
app.include_router(public_router)
app.include_router(queue_router)


@app.get("/", tags=["root"])
async def root():
    return {
        "project": "openMinistry",
        "description": "Public archive of Kerala minister statements",
        "version": "1.0.0",
        "docs": "/docs",
        "api": {
            "statements": "/api/statements",
            "ministers": "/api/ministers",
            "search": "/api/search",
            "topics": "/api/statements/topics",
        },
    }


@app.get("/health", tags=["root"])
async def health_check():
    import time
    start = time.time()
    checks = {}

    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    try:
        from api.cache import get_redis
        r = get_redis()
        if r:
            r.ping()
            checks["redis"] = "connected"
        else:
            checks["redis"] = "unavailable"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    duration = (time.time() - start) * 1000
    status = "healthy" if all(
        "error" not in v for v in checks.values()
    ) else "degraded"

    return {
        "status": status,
        "checks": checks,
        "response_time_ms": round(duration, 2),
    }