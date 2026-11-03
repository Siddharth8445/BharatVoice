import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem
from app.schemas.order import ParsedOrderResponse
from app.services.catalogue import (
    find_product_by_alias,
    get_all_products,
    get_product_by_id,
)
from app.services.order_parser import parse_order_transcript


# ---------------------------------------------------------------------------
# Unit Tests for Grocery Catalogue
# ---------------------------------------------------------------------------

def test_catalogue_initialization_and_categories():
    """Ensure catalogue contains diverse categories and distinct product items."""
    products = get_all_products()
    assert len(products) >= 15

    categories = {p.category for p in products}
    assert "Staples" in categories
    assert "Dairy" in categories
    assert "Pulses" in categories
    assert "Spices" in categories
    assert "Oils" in categories
    assert "Household" in categories
    assert "Packaged Goods" in categories


def test_catalogue_distinct_products_separation():
    """Ensure distinct products (e.g. Atta vs Rice vs Maida) are not merged."""
    atta = find_product_by_alias("atta")
    rice = find_product_by_alias("chawal")
    maida = find_product_by_alias("maida")

    assert atta is not None
    assert rice is not None
    assert maida is not None
    assert atta.product_id != rice.product_id
    assert atta.product_id != maida.product_id
    assert rice.product_id != maida.product_id


def test_catalogue_hindi_and_hinglish_aliases():
    """Verify alias lookup in English, Hinglish, and Devanagari Hindi."""
    milk_en = find_product_by_alias("milk")
    milk_hi = find_product_by_alias("doodh")
    milk_dev = find_product_by_alias("दूध")

    assert milk_en is not None
    assert milk_hi is not None
    assert milk_dev is not None
    assert milk_en.product_id == milk_hi.product_id == milk_dev.product_id == "milk"


# ---------------------------------------------------------------------------
# Unit Tests for Order Parser Service
# ---------------------------------------------------------------------------

def test_single_item_numeric_quantity():
    """Case 1: One item with a standard numeric quantity."""
    res = parse_order_transcript("1 kilo atta")
    assert res.status == "ready_for_review"
    assert res.clarification_required is False
    assert len(res.items) == 1
    assert res.items[0].product_id == "atta"
    assert res.items[0].quantity == 1.0
    assert res.items[0].unit == "kg"


def test_multiple_items_with_conjunction():
    """Case 2: Multiple items joined with 'aur' and conversational polite filler."""
    res = parse_order_transcript("Bhaiya, do kilo atta aur ek litre doodh bhej dena.")
    assert res.status == "ready_for_review"
    assert res.clarification_required is False
    assert len(res.items) == 2

    atta_item = next(it for it in res.items if it.product_id == "atta")
    milk_item = next(it for it in res.items if it.product_id == "milk")

    assert atta_item.quantity == 2.0
    assert atta_item.unit == "kg"
    assert milk_item.quantity == 1.0
    assert milk_item.unit == "litre"


def test_spoken_hindi_quantity_words():
    """Case 3: Hindi spoken quantity words (teen, dedh, dhai)."""
    res = parse_order_transcript("Teen kilo aata aur dedh litre doodh")
    assert res.status == "ready_for_review"
    assert len(res.items) == 2

    atta_item = next(it for it in res.items if it.product_id == "atta")
    milk_item = next(it for it in res.items if it.product_id == "milk")

    assert atta_item.quantity == 3.0
    assert atta_item.unit == "kg"
    assert milk_item.quantity == 1.5
    assert milk_item.unit == "litre"

    # Test dhai (2.5)
    res2 = parse_order_transcript("dhai kilo chawal")
    assert res2.items[0].quantity == 2.5
    assert res2.items[0].product_id == "rice"


def test_decimal_quantities():
    """Case 4: Decimal quantities (e.g. 1.5, 2.5)."""
    res = parse_order_transcript("1.5 litre milk aur 2.5 kg rice")
    assert res.status == "ready_for_review"
    assert len(res.items) == 2

    assert res.items[0].quantity in [1.5, 2.5]
    assert res.items[1].quantity in [1.5, 2.5]


def test_gram_and_packet_units():
    """Case 5: Gram and packet units."""
    res = parse_order_transcript("500 gram cheeni aur 2 packet biscuit")
    assert res.status == "ready_for_review"
    assert len(res.items) == 2

    sugar = next(it for it in res.items if it.product_id == "sugar")
    biscuits = next(it for it in res.items if it.product_id == "biscuits")

    assert sugar.quantity == 500.0
    assert sugar.unit == "g"
    assert biscuits.quantity == 2.0
    assert biscuits.unit == "packet"


def test_devanagari_hindi_transcript():
    """Case 6: Pure Devanagari Hindi transcript."""
    res = parse_order_transcript("दो किलो आटा और एक लीटर दूध")
    assert res.status == "ready_for_review"
    assert len(res.items) == 2
    assert res.items[0].product_id in ["atta", "milk"]
    assert res.items[1].product_id in ["atta", "milk"]

def test_exact_bharatvoice_hindi_voice_order():
    """Regression: extract atta and milk from a Hindi voice order."""

    res = parse_order_transcript(
        "भैया, दो किलो आटा और एक लीटर दूध भेज दो।"
    )

    assert res.status == "ready_for_review"
    assert res.clarification_required is False
    assert len(res.items) == 2

    atta = next(item for item in res.items if item.product_id == "atta")
    milk = next(item for item in res.items if item.product_id == "milk")

    assert atta.quantity == 2.0
    assert atta.unit == "kg"

    assert milk.quantity == 1.0
    assert milk.unit == "litre"


def test_hindi_concatenated_products_without_conjunction():
    """Regression: extract multiple Hindi products even without aur."""

    res = parse_order_transcript(
        "दो किलो आटा एक लीटर दूध"
    )

    assert res.status == "ready_for_review"
    assert len(res.items) == 2

    atta = next(item for item in res.items if item.product_id == "atta")
    milk = next(item for item in res.items if item.product_id == "milk")

    assert atta.quantity == 2.0
    assert atta.unit == "kg"

    assert milk.quantity == 1.0
    assert milk.unit == "litre"    


def test_hinglish_product_aliases():
    """Case 7: Hinglish aliases (sarson tel, cheeni, arhar dal)."""
    res = parse_order_transcript("ek litre sarson tel aur aadha kilo arhar dal")
    assert res.status == "ready_for_review"
    assert len(res.items) == 2

    oil = next(it for it in res.items if it.product_id == "mustard_oil")
    dal = next(it for it in res.items if it.product_id == "arhar_dal")

    assert oil.quantity == 1.0
    assert oil.unit == "litre"
    assert dal.quantity == 0.5
    assert dal.unit == "kg"


def test_missing_quantity_triggers_clarification():
    """Case 8: Missing quantity (e.g., 'atta le aana')."""
    res = parse_order_transcript("atta le aana bhaiya")
    assert res.status == "needs_clarification"
    assert res.clarification_required is True
    assert "Missing quantity for 'Atta'" in res.clarification_message


def test_vague_quantity_triggers_clarification():
    """Case 9: Vague quantity (e.g., 'thoda namak')."""
    res = parse_order_transcript("thoda namak de do")
    assert res.status == "needs_clarification"
    assert res.clarification_required is True
    assert "Vague quantity" in res.clarification_message


def test_unsupported_product_detection():
    """Case 10: Product absent from catalogue (e.g., 'do kilo seb')."""
    res = parse_order_transcript("do kilo seb de do")
    assert res.status == "needs_clarification"
    assert res.clarification_required is True
    assert "seb" in res.unsupported_products


def test_unrecognized_quantity_words():
    """Case 11: Unrecognized / vague quantity word."""
    res = parse_order_transcript("bohot saara atta")
    assert res.status == "needs_clarification"
    assert res.clarification_required is True


def test_empty_transcript_handling():
    """Case 12: Empty transcript handling."""
    res = parse_order_transcript("")
    assert res.status == "needs_clarification"
    assert res.clarification_required is True
    assert "Empty" in res.clarification_message


def test_malformed_transcript_handling():
    """Case 13: Malformed transcript with punctuation or non-grocery conversation."""
    res = parse_order_transcript("... ??? !!!")
    assert res.status == "needs_clarification"
    assert res.clarification_required is True

    res2 = parse_order_transcript("Namaste bhaiya dukaan kab khulegi")
    assert res2.status == "needs_clarification"
    assert "No grocery items" in res2.clarification_message


def test_mixed_valid_and_unsupported_products():
    """Case 14: Mixed valid and unsupported products."""
    res = parse_order_transcript("do kilo atta aur ek kilo amrood")
    # Valid item is extracted
    assert len(res.items) == 1
    assert res.items[0].product_id == "atta"
    # Unsupported product is flagged
    assert "amrood" in res.unsupported_products
    # Overall order state requires clarification before confirmation
    assert res.status == "needs_clarification"
    assert res.clarification_required is True


def test_ambiguous_multi_item_order():
    """Case 15: One item valid, second item ambiguous with vague quantity."""
    res = parse_order_transcript("do kilo atta aur thoda namak")
    assert len(res.items) == 1
    assert res.items[0].product_id == "atta"
    assert res.status == "needs_clarification"
    assert res.clarification_required is True
    assert "Vague quantity" in res.clarification_message


def test_invalid_unit_for_product():
    """Case 16: Unit incompatible with product (e.g. 2 litre atta)."""
    res = parse_order_transcript("do litre atta")
    assert res.status == "needs_clarification"
    assert res.clarification_required is True
    assert "not standard" in res.clarification_message


def test_excessively_long_transcript():
    """Case 17: Transcript exceeding maximum 1000 characters."""
    long_text = "ek kilo atta " * 100
    res = parse_order_transcript(long_text)
    assert res.status == "needs_clarification"
    assert res.clarification_required is True
    assert "maximum supported length" in res.clarification_message


# ---------------------------------------------------------------------------
# API Endpoint Integration Tests (POST /api/orders/parse)
# ---------------------------------------------------------------------------

def test_api_parse_endpoint_success(client: TestClient):
    """Case 18 & 19: Verify POST /api/orders/parse returns structured response without DB writes."""
    payload = {"transcript": "Bhaiya, do kilo atta aur ek litre doodh bhej dena."}
    response = client.post("/api/orders/parse", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "ready_for_review"
    assert data["clarification_required"] is False
    assert data["clarification_message"] is None
    assert len(data["items"]) == 2

    item1 = data["items"][0]
    assert "product_id" in item1
    assert "name" in item1
    assert "quantity" in item1
    assert "unit" in item1
    assert item1["quantity"] > 0


def test_api_parse_does_not_persist_or_confirm_order(client: TestClient, db_session: Session):
    """Case 19: Pure parsing operation must NEVER create or confirm a database order."""
    initial_orders_count = db_session.query(Order).count()
    initial_items_count = db_session.query(OrderItem).count()

    response = client.post(
        "/api/orders/parse",
        json={"transcript": "ek kilo chawal aur do packet biscuit"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify no records were inserted into the SQLite database
    assert db_session.query(Order).count() == initial_orders_count
    assert db_session.query(OrderItem).count() == initial_items_count


def test_api_parse_validation_error_on_empty_payload(client: TestClient):
    """Verify validation error (422) on empty transcript string."""
    response = client.post("/api/orders/parse", json={"transcript": "   "})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
def test_invalid_unit_preserves_product_for_shopkeeper_review():
    result = parse_order_transcript(
        "भैया, दो किलो आटा और एक किलो दूध भेज दो।"
    )

    assert result.clarification_required is True
    assert result.status == "needs_clarification"

    assert len(result.items) == 2

    atta = next(
        item for item in result.items
        if item.product_id == "atta"
    )

    milk = next(
        item for item in result.items
        if item.product_id == "milk"
    )

    assert atta.quantity == 2.0
    assert atta.unit == "kg"

    # Preserve the customer's original request.
    assert milk.quantity == 1.0
    assert milk.unit == "kg"

    assert "not standard" in result.clarification_message    
