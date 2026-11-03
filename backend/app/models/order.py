
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
    func,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Order(Base):
    """SQLAlchemy model representing a customer order at a Kirana store."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transcript = Column(Text, nullable=False, default="")
    status = Column(String(32), nullable=False, default="pending", index=True)

    # Persistent clarification information
    clarification_required = Column(Boolean, nullable=False, default=False)
    clarification_message = Column(Text, nullable=True)
    unsupported_products = Column(JSON, nullable=False, default=list)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, status='{self.status}')>"


class OrderItem(Base):
    """SQLAlchemy model representing a specific item in an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_name = Column(String(255), nullable=False)
    product_id = Column(String(100), nullable=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    unit_price = Column(Float, nullable=True)

    order = relationship("Order", back_populates="items")

    def __repr__(self) -> str:
        return (
            f"<OrderItem(id={self.id}, product='{self.product_name}', "
            f"qty={self.quantity} {self.unit})>"
        )

