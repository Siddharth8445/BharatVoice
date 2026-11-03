import io
import wave


def make_test_wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\\x00\\x00" * 1600)
    return buffer.getvalue()


def test_voice_order_creates_reviewable_order_and_requires_explicit_confirmation(client):
    audio = make_test_wav()
    response = client.post(
        "/api/orders/voice",
        files={"audio_file": ("customer-order.wav", audio, "audio/wav")},
    )

    assert response.status_code == 201, response.text
    order = response.json()
    assert order["status"] == "awaiting_confirmation"
    assert order["transcript"]
    assert len(order["items"]) >= 1

    # Voice processing creates a reviewable order, never a confirmed order.
    assert order["status"] != "confirmed"

    confirm_response = client.post(f"/api/orders/{order['id']}/confirm")
    assert confirm_response.status_code == 200, confirm_response.text
    assert confirm_response.json()["status"] == "confirmed"


def test_clarification_order_becomes_reviewable_after_shopkeeper_adds_items(client, monkeypatch):
    from app.schemas.order import ParsedOrderResponse
    from app.services import order_parser

    monkeypatch.setattr(
        order_parser,
        "parse_order_transcript",
        lambda _transcript: ParsedOrderResponse(
            items=[],
            status="needs_clarification",
            clarification_required=True,
            clarification_message="Please specify the product quantity.",
            unsupported_products=[],
        ),
    )

    audio = make_test_wav()
    created = client.post(
        "/api/orders/voice",
        files={"audio_file": ("customer-order.wav", audio, "audio/wav")},
    )
    assert created.status_code == 201, created.text
    order = created.json()
    assert order["status"] == "needs_clarification"

    edited = client.patch(
        f"/api/orders/{order['id']}",
        json={"items": [{"product_name": "Atta", "quantity": 2, "unit": "kg"}]},
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["status"] == "awaiting_confirmation"
    assert len(edited.json()["items"]) == 1
