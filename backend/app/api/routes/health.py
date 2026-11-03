import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=None)
def get_health(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Health check endpoint verifying application state, environment,

    database connectivity, and Gnani integration mode.
    """
    db_status = "unknown"
    is_healthy = True

    try:
        # Lightweight database verification query
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            db_status = "connected"
        else:
            db_status = "unexpected_response"
            is_healthy = False
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        db_status = "disconnected"
        is_healthy = False

    payload: Dict[str, Any] = {
        "status": "healthy" if is_healthy else "unhealthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "use_mock_gnani": settings.is_gnani_mock_enabled,
    }

    if not is_healthy:
        payload["error"] = "Database connection failed"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload,
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=payload,
    )
