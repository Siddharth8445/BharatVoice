from unittest.mock import MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.core.config import get_settings
from app.db.session import get_db, init_db, Base
from app.main import app
from app.models.order import Order, OrderItem


def test_health_endpoint_healthy(client: TestClient):
    """Verify GET /api/health returns 200 with structured health payload."""
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "BharatVoice"
    assert data["environment"] == "development"
    assert data["database"] == "connected"
    assert "use_mock_gnani" in data
    assert isinstance(data["use_mock_gnani"], bool)

    # Critical security check: API key and secrets must NEVER be present
    assert "api_key" not in data
    assert "GNANI_API_KEY" not in data
    assert "key" not in data


def test_health_endpoint_db_failure():
    """Verify GET /api/health returns 503 when the database is unavailable."""
    def _failing_get_db():
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Simulated DB connection lost")
        yield mock_session

    app.dependency_overrides[get_db] = _failing_get_db
    try:
        with TestClient(app) as test_client:
            response = test_client.get("/api/health")
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"
            assert data["error"] == "Database connection failed"
    finally:
        app.dependency_overrides.clear()


def test_database_table_initialization(db_session, test_engine):
    """Verify that models Order and OrderItem are initialized properly and support relationships."""
    # Create an order with items in the test database
    new_order = Order(
        transcript="Bhaiya do kilo atta aur ek packet namak",
        status="pending",
    )
    db_session.add(new_order)
    db_session.commit()
    db_session.refresh(new_order)

    assert new_order.id is not None
    assert new_order.status == "pending"

    # Add items to order
    item1 = OrderItem(
        order_id=new_order.id,
        product_name="Atta",
        quantity=2.0,
        unit="kg",
        unit_price=45.0,
    )
    item2 = OrderItem(
        order_id=new_order.id,
        product_name="Namak",
        quantity=1.0,
        unit="packet",
        unit_price=25.0,
    )
    db_session.add_all([item1, item2])
    db_session.commit()
    db_session.refresh(new_order)

    # Verify relationship loaded properly
    assert len(new_order.items) == 2
    assert new_order.items[0].product_name in ["Atta", "Namak"]
    assert new_order.items[0].quantity > 0

    # Test cascade delete: deleting order deletes line items
    db_session.delete(new_order)
    db_session.commit()

    remaining_items = db_session.query(OrderItem).filter(OrderItem.order_id == new_order.id).all()
    assert len(remaining_items) == 0


def test_root_endpoint(client: TestClient):
    """Verify root / endpoint returns welcome status and mock indicator."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Welcome to BharatVoice API"
    assert data["health_check"] == "/api/health"
