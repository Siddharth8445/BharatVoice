
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderItemBase(BaseModel):
    product_name: str = Field(
        ..., min_length=1, max_length=255,
        description="Name of the product",
    )
    product_id: Optional[str] = Field(
        None, max_length=100,
        description="Optional catalogue product ID",
    )
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)
    unit_price: Optional[float] = Field(None, ge=0)

    @field_validator("quantity")
    @classmethod
    def validate_positive_quantity(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Quantity must be greater than zero")
        return round(value, 3)

    @field_validator("product_name", "unit")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty or only whitespace")
        return value


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    transcript: str = ""
    status: str = "pending"


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(default_factory=list)


class OrderResponse(OrderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = Field(default_factory=list)

    # Phase 8 clarification information
    clarification_required: bool = False
    clarification_message: Optional[str] = None
    unsupported_products: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TranscriptParseRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=1000)

    @field_validator("transcript")
    @classmethod
    def validate_non_empty_transcript(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Transcript cannot be empty")
        return value


class ParsedOrderItem(BaseModel):
    product_id: str
    name: str
    quantity: float = Field(..., gt=0)
    unit: str
    unit_price: Optional[float] = Field(None, ge=0)

    def to_order_item_create(self) -> OrderItemCreate:
        return OrderItemCreate(
            product_name=self.name,
            product_id=self.product_id,
            quantity=self.quantity,
            unit=self.unit,
            unit_price=self.unit_price,
        )


class ParsedOrderResponse(BaseModel):
    items: List[ParsedOrderItem] = Field(default_factory=list)
    status: str = "ready_for_review"
    clarification_required: bool = False
    clarification_message: Optional[str] = None
    unsupported_products: List[str] = Field(default_factory=list)


