from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import get_settings

settings = get_settings()

# For SQLite, check_same_thread=False is required for multithreaded FastAPI requests
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db(target_engine=None) -> None:
    """Create all tables in the database if they do not exist."""
    # Import all models here so that Base.metadata has them registered
    import app.models.order  # noqa: F401

    bind_engine = target_engine or engine
    Base.metadata.create_all(bind=bind_engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session and ensures it is properly closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
