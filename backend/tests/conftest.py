
import os
import tempfile
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import Settings, get_settings
from app.db.session import Base, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def force_mock_gnani():
    """Keep automated tests independent of live Gnani credentials."""
    os.environ["USE_MOCK_GNANI"] = "true"
    get_settings.cache_clear()

    yield

    os.environ.pop("USE_MOCK_GNANI", None)
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary SQLite database for the test session."""
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_bharatvoice_")
    os.close(fd)

    yield path

    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@pytest.fixture(scope="session")
def test_engine(test_db_path: str):
    """Engine bound to the temporary test database."""
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide a transactional database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
    )
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient using the isolated test database."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
