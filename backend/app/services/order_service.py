
import logging
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.models import order as order_model
from app.services import speech_to_text, order_parser
from app.services.catalogue import (
    find_product_by_alias,
    get_product_by_id,
)
from app.services.order_parser import UNIT_MAPPINGS

logger = logging.getLogger(__name__)

STATUS_DRAFT = "draft"
STATUS_NEEDS_CLARIFICATION = "needs_clarification"
STATUS_AWAITING_CONFIRMATION = "awaiting_confirmation"
STATUS_CONFIRMED = "confirmed"
STATUS_CANCELLED = "cancelled"


VALID_TRANSITIONS = {
    STATUS_DRAFT: {
        STATUS_NEEDS_CLARIFICATION,
        STATUS_AWAITING_CONFIRMATION,
    },
    STATUS_NEEDS_CLARIFICATION: {
        STATUS_AWAITING_CONFIRMATION,
    },
    STATUS_AWAITING_CONFIRMATION: {
        STATUS_CONFIRMED,
        STATUS_CANCELLED,
        STATUS_NEEDS_CLARIFICATION,
    },
    STATUS_CONFIRMED: set(),
    STATUS_CANCELLED: set(),
}


def _assert_transition(current: str, target: str) -> None:
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid state transition from '{current}' "
                f"to '{target}'."
            ),
        )


def _resolve_catalogue_product(item):
    """Resolve an item against the canonical grocery catalogue."""

    product = None

    if item.product_id:
        product = get_product_by_id(item.product_id)

    if product is None:
        product = find_product_by_alias(item.product_name)

    return product


def _validate_order_items(
    items,
) -> Tuple[List[str], List[str]]:
    """
    Validate all order items against the catalogue.

    Returns:
        errors: Human-readable validation errors.
        unsupported: Product names not found in the catalogue.
    """

    errors = []
    unsupported = []

    for index, item in enumerate(items, start=1):
        product = _resolve_catalogue_product(item)

        if product is None:
            unsupported.append(item.product_name)
            errors.append(
                f"Product '{item.product_name}' is not in the "
                "Kirana catalogue. Please select a supported product."
            )
            continue

        normalized_unit = UNIT_MAPPINGS.get(
            item.unit.strip().lower(),
            item.unit.strip().lower(),
        )

        if normalized_unit not in product.allowed_units:
            errors.append(
                f"Unit '{item.unit}' is not valid for "
                f"'{product.name}'. Supported units: "
                f"{', '.join(product.allowed_units)}."
            )

        if item.quantity <= 0:
            errors.append(
                f"Quantity for '{product.name}' must be greater than zero."
            )

    return errors, unsupported


def _populate_response(order_obj) -> schemas.OrderResponse:
    """Build a complete order response including clarification details."""

    response = schemas.OrderResponse.model_validate(order_obj)

    response.items = [
        schemas.OrderItemResponse.model_validate(item)
        for item in order_obj.items
    ]

    return response


async def create_order_from_voice(
    db: Session,
    audio_bytes: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> schemas.OrderResponse:
    """Transcribe audio, parse the order, and persist its details."""

    # 1. Speech-to-text
    stt_service = speech_to_text.get_speech_to_text_service()

    transcription = await stt_service.transcribe(
        audio_bytes=audio_bytes,
        filename=filename,
        content_type=content_type,
    )

    # 2. Deterministic order parsing
    parsed = order_parser.parse_order_transcript(
        transcription.transcript
    )

    # 3. Initial status
    if parsed.clarification_required:
        order_status = STATUS_NEEDS_CLARIFICATION
    else:
        order_status = STATUS_AWAITING_CONFIRMATION

    # 4. Create order with persistent clarification details
    order_obj = order_model.Order(
        transcript=transcription.transcript,
        status=order_status,
        clarification_required=parsed.clarification_required,
        clarification_message=parsed.clarification_message,
        unsupported_products=parsed.unsupported_products or [],
    )

    try:
        db.add(order_obj)
        db.flush()

        # 5. Persist every extracted item, including items
        # whose units need correction.
        for parsed_item in parsed.items:
            db_item = order_model.OrderItem(
                order_id=order_obj.id,
                product_name=parsed_item.name,
                product_id=parsed_item.product_id,
                quantity=parsed_item.quantity,
                unit=parsed_item.unit,
                unit_price=parsed_item.unit_price,
            )
            db.add(db_item)

        db.commit()
        db.refresh(order_obj)

        return _populate_response(order_obj)

    except Exception:
        db.rollback()
        logger.exception("Failed to create voice order")
        raise


def get_order(
    db: Session,
    order_id: int,
) -> schemas.OrderResponse:

    order_obj = (
        db.query(order_model.Order)
        .filter(order_model.Order.id == order_id)
        .first()
    )

    if not order_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    return _populate_response(order_obj)


def list_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
) -> List[schemas.OrderResponse]:

    query = db.query(order_model.Order)

    if status_filter:
        query = query.filter(
            order_model.Order.status == status_filter
        )

    orders = (
        query.order_by(order_model.Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [_populate_response(order) for order in orders]


def edit_order_items(
    db: Session,
    order_id: int,
    items: List[schemas.OrderItemCreate],
) -> schemas.OrderResponse:

    order_obj = (
        db.query(order_model.Order)
        .filter(order_model.Order.id == order_id)
        .first()
    )

    if not order_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    editable_statuses = {
        STATUS_DRAFT,
        STATUS_NEEDS_CLARIFICATION,
        STATUS_AWAITING_CONFIRMATION,
    }

    if order_obj.status not in editable_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a confirmed or cancelled order.",
        )

    if not items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An order must contain at least one item.",
        )

    # Validate before replacing any existing database items.
    errors, unsupported = _validate_order_items(items)

    try:
        db.query(order_model.OrderItem).filter(
            order_model.OrderItem.order_id == order_id
        ).delete(synchronize_session=False)

        for item_data in items:
            product = _resolve_catalogue_product(item_data)

            normalized_unit = UNIT_MAPPINGS.get(
                item_data.unit.strip().lower(),
                item_data.unit.strip().lower(),
            )

            db_item = order_model.OrderItem(
                order_id=order_id,
                product_name=(
                    product.name if product else item_data.product_name
                ),
                product_id=(
                    product.product_id if product else item_data.product_id
                ),
                quantity=item_data.quantity,
                unit=normalized_unit,
                unit_price=(
                    item_data.unit_price
                    if item_data.unit_price is not None
                    else (
                        product.typical_unit_price
                        if product else None
                    )
                ),
            )

            db.add(db_item)

        # Invalid corrections remain unresolved.
        if errors:
            order_obj.status = STATUS_NEEDS_CLARIFICATION
            order_obj.clarification_required = True
            order_obj.clarification_message = " ".join(errors)
            order_obj.unsupported_products = unsupported

        else:
            # Valid corrections can proceed to review.
            if order_obj.status in {
                STATUS_NEEDS_CLARIFICATION,
                STATUS_DRAFT,
            }:
                order_obj.status = STATUS_AWAITING_CONFIRMATION

            order_obj.clarification_required = False
            order_obj.clarification_message = None
            order_obj.unsupported_products = []

        db.commit()
        db.refresh(order_obj)

        return _populate_response(order_obj)

    except Exception:
        db.rollback()
        logger.exception(
            "Failed to edit order %s",
            order_id,
        )
        raise


def confirm_order(
    db: Session,
    order_id: int,
) -> schemas.OrderResponse:

    order_obj = (
        db.query(order_model.Order)
        .filter(order_model.Order.id == order_id)
        .first()
    )

    if not order_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    if order_obj.status == STATUS_NEEDS_CLARIFICATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                order_obj.clarification_message
                or "Resolve order clarification before confirmation."
            ),
        )

    if not order_obj.items:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot confirm an order without items.",
        )

    errors, unsupported = _validate_order_items(order_obj.items)

    if errors:
        order_obj.status = STATUS_NEEDS_CLARIFICATION
        order_obj.clarification_required = True
        order_obj.clarification_message = " ".join(errors)
        order_obj.unsupported_products = unsupported

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=order_obj.clarification_message,
        )

    _assert_transition(
        order_obj.status,
        STATUS_CONFIRMED,
    )

    order_obj.status = STATUS_CONFIRMED
    order_obj.clarification_required = False
    order_obj.clarification_message = None
    order_obj.unsupported_products = []

    db.commit()
    db.refresh(order_obj)

    return _populate_response(order_obj)


def cancel_order(
    db: Session,
    order_id: int,
) -> schemas.OrderResponse:

    order_obj = (
        db.query(order_model.Order)
        .filter(order_model.Order.id == order_id)
        .first()
    )

    if not order_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    _assert_transition(
        order_obj.status,
        STATUS_CANCELLED,
    )

    order_obj.status = STATUS_CANCELLED

    db.commit()
    db.refresh(order_obj)

    return _populate_response(order_obj)

