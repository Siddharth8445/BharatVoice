
from sqlalchemy import inspect, text

from app.db.session import engine


def migrate():
    if engine.dialect.name != "sqlite":
        raise RuntimeError("This migration is intended for SQLite.")

    inspector = inspect(engine)
    existing_columns = {
        column["name"]
        for column in inspector.get_columns("orders")
    }

    migrations = {
        "clarification_required": (
            "ALTER TABLE orders ADD COLUMN "
            "clarification_required BOOLEAN NOT NULL DEFAULT 0"
        ),
        "clarification_message": (
            "ALTER TABLE orders ADD COLUMN clarification_message TEXT"
        ),
        "unsupported_products": (
            "ALTER TABLE orders ADD COLUMN "
            "unsupported_products JSON NOT NULL DEFAULT '[]'"
        ),
    }

    with engine.begin() as connection:
        for column_name, sql in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(sql))
                print(f"Added column: {column_name}")
            else:
                print(f"Already exists: {column_name}")

    print("Phase 8 database migration completed.")


if __name__ == "__main__":
    migrate()
