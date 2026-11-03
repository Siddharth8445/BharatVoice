import logging
import io
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.schemas.order import (
    ParsedOrderResponse,
    TranscriptParseRequest,
    OrderResponse,
    OrderItemCreate,
)
from app.services import order_service
from app.services.text_to_speech import get_text_to_speech_service
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])

# ---------------------------------------------------------------------
# 1. Parse transcript only (no DB side‑effects) – kept for compatibility
# ---------------------------------------------------------------------
@router.post(
    "/parse",
    response_model=ParsedOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse Hindi/Hinglish audio transcript into structured grocery items",
)
def parse_transcript(payload: TranscriptParseRequest) -> ParsedOrderResponse:
    """Parse a raw transcript without persisting anything."""
    try:
        # Use deterministic parser directly
        from app.services.order_parser import parse_order_transcript
        return parse_order_transcript(payload.transcript)
    except Exception as exc:
        logger.error("Parse error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse transcript.",
        )

# ---------------------------------------------------------------------
# 2. Voice order creation – upload audio, transcribe, parse, store order
# ---------------------------------------------------------------------
@router.post(
    "/voice",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload voice audio, run STT, parse and create a draft order",
)
async def create_order_from_voice(
    audio_file: UploadFile = File(..., description="Customer audio (WAV/MP3/etc.)"),
    db: Session = Depends(get_db),
) -> OrderResponse:
    audio_bytes = await audio_file.read()
    order = await order_service.create_order_from_voice(
        db=db,
        audio_bytes=audio_bytes,
        filename=audio_file.filename,
        content_type=audio_file.content_type,
    )
    return order

# ---------------------------------------------------------------------
# 3. Retrieve a single order
# ---------------------------------------------------------------------
@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details by ID",
)
def get_order_endpoint(order_id: int, db: Session = Depends(get_db)) -> OrderResponse:
    return order_service.get_order(db, order_id)

# ---------------------------------------------------------------------
# 4. List orders with optional status filter & pagination
# ---------------------------------------------------------------------
@router.get(
    "",
    response_model=List[OrderResponse],
    summary="List orders (optional status filter, pagination)",
)
def list_orders_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[OrderResponse]:
    return order_service.list_orders(db, skip=skip, limit=limit, status_filter=status_filter)

# ---------------------------------------------------------------------
# 5. Edit order items before confirmation
# ---------------------------------------------------------------------
@router.patch(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Edit order items while draft/clarification",
)
def edit_order_items_endpoint(
    order_id: int,
    items: List[OrderItemCreate] = Body(..., embed=True),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return order_service.edit_order_items(db, order_id, items)

# ---------------------------------------------------------------------
# 6. Confirm order explicitly
# ---------------------------------------------------------------------
@router.post(
    "/{order_id}/confirm",
    response_model=OrderResponse,
    summary="Explicitly confirm a pending order",
)
def confirm_order_endpoint(order_id: int, db: Session = Depends(get_db)) -> OrderResponse:
    return order_service.confirm_order(db, order_id)

# ---------------------------------------------------------------------
# 7. Cancel unconfirmed order
# ---------------------------------------------------------------------
@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel an unconfirmed order",
)
def cancel_order_endpoint(order_id: int, db: Session = Depends(get_db)) -> OrderResponse:
    return order_service.cancel_order(db, order_id)

# ---------------------------------------------------------------------
# 8. Generate spoken confirmation for a confirmed order
# ---------------------------------------------------------------------
def _build_confirmation_message(order_obj) -> str:
    parts = []

    for item in order_obj.items:
        quantity = float(item.quantity)

        if quantity.is_integer():
            quantity = int(quantity)

        parts.append(f"{item.product_name}, {quantity} {item.unit}")

    items_text = " और ".join(parts)

    return (
        f"आपका ऑर्डर सफलतापूर्वक कन्फर्म हो गया है। "
        f"आपने ऑर्डर किया है: {items_text}।"
    )


# ---------------------------------------------------------------------
# 9. Generate spoken confirmation for a confirmed order
# ---------------------------------------------------------------------
@router.post(
    "/{order_id}/speak-confirmation",
    summary="Generate Hindi audio confirmation for a confirmed order",
    response_class=StreamingResponse,
)
async def speak_order_confirmation(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = order_service.get_order(db, order_id)

    if order.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only confirmed orders can generate a spoken confirmation.",
        )

    confirmation_text = _build_confirmation_message(order)

    tts_service = get_text_to_speech_service()

    audio_bytes = await tts_service.synthesize(
        text=confirmation_text,
        language="hi-IN",
    )

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={
            "Content-Disposition": (
                f'inline; filename="order-{order_id}-confirmation.wav"'
            )
        },
    )