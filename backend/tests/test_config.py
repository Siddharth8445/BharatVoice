import pytest
from app.core.config import Settings
from app.schemas.order import OrderItemCreate, OrderCreate


def test_default_config_enables_mock_mode():
    """Verify that default settings enable mock mode safely when no key is set."""
    settings = Settings(GNANI_API_KEY=None, USE_MOCK_GNANI=True)
    assert settings.is_gnani_mock_enabled is True
    assert settings.APP_NAME == "BharatVoice"
    assert settings.ENVIRONMENT == "development"


def test_real_mode_without_api_key_is_not_silently_mocked():
    """Explicit real mode remains real; missing credentials must be reported by the provider service."""
    settings = Settings(GNANI_API_KEY=None, USE_MOCK_GNANI=False)
    assert settings.is_gnani_mock_enabled is False

    settings_empty = Settings(GNANI_API_KEY="   ", USE_MOCK_GNANI=False)
    assert settings_empty.is_gnani_mock_enabled is False


def test_real_mode_when_key_present_and_mock_disabled():
    """Mock mode is disabled only when valid key is provided AND USE_MOCK_GNANI is False."""
    settings = Settings(GNANI_API_KEY="test_real_key_123", USE_MOCK_GNANI=False)
    assert settings.is_gnani_mock_enabled is False


def test_environment_variable_overrides(monkeypatch):
    """Ensure environment variables correctly override default settings."""
    monkeypatch.setenv("PORT", "8888")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://bharatvoice.in,https://app.bharatvoice.in")
    monkeypatch.setenv("MAX_AUDIO_DURATION_SECONDS", "45")

    settings = Settings()
    assert settings.PORT == 8888
    assert settings.HOST == "127.0.0.1"
    assert settings.ENVIRONMENT == "production"
    assert settings.CORS_ORIGINS == ["https://bharatvoice.in", "https://app.bharatvoice.in"]
    assert settings.MAX_AUDIO_DURATION_SECONDS == 45


def test_order_item_schema_rejects_non_positive_quantity():
    """Business rule: quantities must be strictly positive."""
    # Zero quantity should be rejected
    with pytest.raises(ValueError):
        OrderItemCreate(
            product_name="Atta",
            quantity=0,
            unit="kg",
        )

    # Negative quantity should be rejected
    with pytest.raises(ValueError):
        OrderItemCreate(
            product_name="Atta",
            quantity=-2.5,
            unit="kg",
        )


def test_order_item_schema_supports_fractional_quantities():
    """Ensure fractional quantities (e.g. 0.5 kg, 1.25 litre) are valid."""
    item = OrderItemCreate(
        product_name="Doodh",
        quantity=0.5,
        unit="litre",
        unit_price=30.0,
    )
    assert item.quantity == 0.5
    assert item.unit == "litre"
    assert item.product_name == "Doodh"
