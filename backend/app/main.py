import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health_router, orders_router, stt_router
from app.core.config import get_settings
from app.db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bharatvoice")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager handling application startup and shutdown."""
    logger.info("Starting up %s (Environment: %s)", settings.APP_NAME, settings.ENVIRONMENT)
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Database initialized successfully.")
    logger.info("Gnani AI Mock Mode: %s", settings.is_gnani_mock_enabled)

    yield

    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Indian-language voice intelligence assistant for small Indian grocery shops",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(health_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(stt_router, prefix="/api")


@app.get("/", tags=["Root"])
def root_redirect():
    """Root endpoint welcoming clients and directing them to health check or docs."""
    return {
        "message": "Welcome to BharatVoice API",
        "health_check": "/api/health",
        "docs": "/docs",
        "mock_mode": settings.is_gnani_mock_enabled,
    }
