"""API routes package."""
from app.api.routes.health import router as health_router
from app.api.routes.orders import router as orders_router
from app.api.routes.stt import router as stt_router

__all__ = ["health_router", "orders_router", "stt_router"]
