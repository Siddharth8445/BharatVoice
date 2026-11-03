"""Services package for external APIs and business logic."""
from app.services.catalogue import (
    Product,
    find_product_by_alias,
    get_all_products,
    get_product_by_id,
)
from app.services.order_parser import parse_order_transcript

from app.services.speech_to_text import (
    SpeechToTextService,
    get_speech_to_text_service,
    validate_audio_content,
    detect_audio_format,
)

__all__ = [
    "Product",
    "find_product_by_alias",
    "get_all_products",
    "get_product_by_id",
    "parse_order_transcript",
    "SpeechToTextService",
    "get_speech_to_text_service",
    "validate_audio_content",
    "detect_audio_format",
]
