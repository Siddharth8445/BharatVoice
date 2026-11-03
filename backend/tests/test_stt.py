import io
import wave
import httpx
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.schemas.stt import TranscriptionResponse
from app.services.speech_to_text import (
    SpeechToTextService,
    detect_audio_format,
    get_speech_to_text_service,
    validate_audio_content,
)


def make_wav_bytes(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate in-memory valid PCM WAV audio bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        num_frames = int(duration_seconds * sample_rate)
        wf.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Unit Tests for Audio Detection & Validation
# ---------------------------------------------------------------------------

def test_detect_audio_format():
    """Verify detection of various audio format magic bytes."""
    wav_bytes = make_wav_bytes(0.5)
    assert detect_audio_format(wav_bytes) == "wav"

    mp3_id3 = b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x64" + b"\x00" * 50
    assert detect_audio_format(mp3_id3) == "mp3"

    ogg_bytes = b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00" + b"\x00" * 50
    assert detect_audio_format(ogg_bytes) == "ogg"

    flac_bytes = b"fLaC\x00\x00\x00\x22" + b"\x00" * 50
    assert detect_audio_format(flac_bytes) == "flac"

    m4a_bytes = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00M4A mp42isom" + b"\x00" * 50
    assert detect_audio_format(m4a_bytes) == "m4a"

    webm_bytes = b"\x1a\x45\xdf\xa3" + b"\x00" * 50
    assert detect_audio_format(webm_bytes) == "webm"

    assert detect_audio_format(b"not an audio header") is None
    assert detect_audio_format(b"") is None


def test_validate_audio_rejects_empty():
    """Empty files must raise 400 Bad Request."""
    with pytest.raises(Exception) as excinfo:
        validate_audio_content(b"")
    assert "empty" in str(excinfo.value.detail).lower()


def test_validate_audio_rejects_unsupported():
    """Files with non-audio signatures must raise 400 Bad Request."""
    with pytest.raises(Exception) as excinfo:
        validate_audio_content(b"<html><body>Fake Audio</body></html>")
    assert "unsupported or invalid" in str(excinfo.value.detail).lower()


def test_validate_audio_rejects_oversized():
    """Files exceeding size limit must raise 413 Request Entity Too Large."""
    dummy_wav = make_wav_bytes(0.5)
    # Set limit smaller than dummy_wav
    with pytest.raises(Exception) as excinfo:
        validate_audio_content(dummy_wav, max_file_size=len(dummy_wav) - 10)
    assert excinfo.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


def test_validate_audio_rejects_duration_exceeded():
    """WAV files exceeding 30s duration must be rejected with 400."""
    long_wav = make_wav_bytes(duration_seconds=31.0)
    with pytest.raises(Exception) as excinfo:
        validate_audio_content(long_wav, max_duration_seconds=30)
    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds maximum allowed limit" in str(excinfo.value.detail)


def test_validate_audio_rejects_corrupted_wav():
    """Corrupted WAV headers must raise 400 Bad Request."""
    corrupt_wav = b"RIFF\x10\x00\x00\x00WAVEfmt \x10\x00\x00\x00corrupted_bytes"
    with pytest.raises(Exception) as excinfo:
        validate_audio_content(corrupt_wav)
    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Unit & Integration Tests for SpeechToTextService (Mock & Real Modes)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stt_service_mock_mode():
    """In mock mode, service returns realistic transcript without upstream calls."""
    settings = Settings(USE_MOCK_GNANI=True, GNANI_API_KEY=None)
    service = SpeechToTextService(settings=settings)

    wav = make_wav_bytes(1.0)
    result = await service.transcribe(wav, filename="order.wav")

    assert isinstance(result, TranscriptionResponse)
    assert result.success is True
    assert result.provider_mode == "mock"
    assert "atta" in result.transcript.lower() or "doodh" in result.transcript.lower()
    assert result.model == settings.GNANI_STT_MODEL
    assert result.request_id.startswith("mock-stt-")


@pytest.mark.asyncio
async def test_stt_service_real_mode_missing_api_key():
    """If real mode is explicitly enabled (USE_MOCK_GNANI=False) without an API key, raise 500 configuration error."""
    settings = Settings(USE_MOCK_GNANI=False, GNANI_API_KEY="")
    service = SpeechToTextService(settings=settings)

    with pytest.raises(Exception) as excinfo:
        await service.transcribe(make_wav_bytes(1.0))

    assert excinfo.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "api key is not configured" in str(excinfo.value.detail).lower()


@pytest.mark.asyncio
async def test_stt_service_real_mode_success():
    """Simulate successful upstream 200 response from Gnani API."""
    settings = Settings(
        USE_MOCK_GNANI=False,
        GNANI_API_KEY="test_gnani_secret_key_12345",
        GNANI_STT_ENDPOINT="https://api.vachana.ai/stt/v3",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("X-API-Key-ID") == "test_gnani_secret_key_12345"
        assert "audio_file" in str(request.read())
        return httpx.Response(
            status_code=200,
            json={
                "success": True,
                "request_id": "gnani-req-9988",
                "transcript": "दो किलो आटा और एक लीटर दूध",
                "model": "prisma-v3.0",
                "detected_language_code": "hi-IN",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = SpeechToTextService(settings=settings, http_client=client)
        result = await service.transcribe(make_wav_bytes(1.0))

        assert result.success is True
        assert result.provider_mode == "real"
        assert result.transcript == "दो किलो आटा और एक लीटर दूध"
        assert result.detected_language_code == "hi-IN"
        assert result.request_id == "gnani-req-9988"


@pytest.mark.asyncio
async def test_stt_service_upstream_auth_error():
    """Upstream 401 Unauthorized returns 502 without leaking API key."""
    secret = "super_secret_key_9999"
    settings = Settings(USE_MOCK_GNANI=False, GNANI_API_KEY=secret)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=401, json={"message": "Unauthorized API key"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = SpeechToTextService(settings=settings, http_client=client)
        with pytest.raises(Exception) as excinfo:
            await service.transcribe(make_wav_bytes(1.0))

        assert excinfo.value.status_code == status.HTTP_502_BAD_GATEWAY
        assert "authentication failed" in str(excinfo.value.detail).lower()
        # Verify secret is NEVER leaked
        assert secret not in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_stt_service_upstream_rate_limit():
    """Upstream 429 Too Many Requests returns 429."""
    settings = Settings(USE_MOCK_GNANI=False, GNANI_API_KEY="valid_key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=429, json={"message": "Rate limit exceeded"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = SpeechToTextService(settings=settings, http_client=client)
        with pytest.raises(Exception) as excinfo:
            await service.transcribe(make_wav_bytes(1.0))

        assert excinfo.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.asyncio
async def test_stt_service_upstream_server_error():
    """Upstream 500/503 returns 502 Bad Gateway."""
    settings = Settings(USE_MOCK_GNANI=False, GNANI_API_KEY="valid_key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = SpeechToTextService(settings=settings, http_client=client)
        with pytest.raises(Exception) as excinfo:
            await service.transcribe(make_wav_bytes(1.0))

        assert excinfo.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_stt_service_upstream_timeout():
    """Upstream timeout returns 504 Gateway Timeout."""
    settings = Settings(USE_MOCK_GNANI=False, GNANI_API_KEY="valid_key")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Connection timed out")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = SpeechToTextService(settings=settings, http_client=client)
        with pytest.raises(Exception) as excinfo:
            await service.transcribe(make_wav_bytes(1.0))

        assert excinfo.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT


@pytest.mark.asyncio
async def test_stt_service_upstream_network_error():
    """Network connection failure returns 502 Bad Gateway."""
    settings = Settings(USE_MOCK_GNANI=False, GNANI_API_KEY="valid_key")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Failed to connect")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = SpeechToTextService(settings=settings, http_client=client)
        with pytest.raises(Exception) as excinfo:
            await service.transcribe(make_wav_bytes(1.0))

        assert excinfo.value.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.asyncio
async def test_stt_service_malformed_json():
    """Upstream returning invalid JSON returns 502."""
    settings = Settings(USE_MOCK_GNANI=False, GNANI_API_KEY="valid_key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, text="<non-json-response>")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = SpeechToTextService(settings=settings, http_client=client)
        with pytest.raises(Exception) as excinfo:
            await service.transcribe(make_wav_bytes(1.0))

        assert excinfo.value.status_code == status.HTTP_502_BAD_GATEWAY
        assert "invalid json" in str(excinfo.value.detail).lower()


@pytest.mark.asyncio
async def test_stt_service_missing_transcript():
    """Upstream 200 response lacking 'transcript' returns 502."""
    settings = Settings(USE_MOCK_GNANI=False, GNANI_API_KEY="valid_key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, json={"success": True, "request_id": "123"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = SpeechToTextService(settings=settings, http_client=client)
        with pytest.raises(Exception) as excinfo:
            await service.transcribe(make_wav_bytes(1.0))

        assert excinfo.value.status_code == status.HTTP_502_BAD_GATEWAY
        assert "missing transcript" in str(excinfo.value.detail).lower()


# ---------------------------------------------------------------------------
# API Endpoint Tests: POST /api/transcribe
# ---------------------------------------------------------------------------

def test_api_transcribe_endpoint_valid_wav(client: TestClient):
    """POST /api/transcribe with valid WAV returns 200 with structured response."""
    wav = make_wav_bytes(1.0)
    files = {"audio_file": ("sample.wav", wav, "audio/wav")}

    response = client.post("/api/transcribe", files=files)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert "transcript" in data
    assert len(data["transcript"]) > 0
    assert data["provider_mode"] == "mock"
    assert data["model"] == "prisma-v3.0"
    assert "request_id" in data


def test_api_transcribe_endpoint_empty_file(client: TestClient):
    """POST /api/transcribe with 0 bytes rejects with 400 Bad Request."""
    files = {"audio_file": ("empty.wav", b"", "audio/wav")}
    response = client.post("/api/transcribe", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in response.json()["detail"].lower()


def test_api_transcribe_endpoint_unsupported_file(client: TestClient):
    """POST /api/transcribe with fake audio rejects with 400."""
    files = {"audio_file": ("fake.wav", b"This is text pretending to be audio.", "audio/wav")}
    response = client.post("/api/transcribe", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "unsupported or invalid" in response.json()["detail"].lower()


def test_api_transcribe_endpoint_duration_violation(client: TestClient):
    """POST /api/transcribe with >30s WAV rejects with 400."""
    long_wav = make_wav_bytes(duration_seconds=32.0)
    files = {"audio_file": ("long.wav", long_wav, "audio/wav")}
    response = client.post("/api/transcribe", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds maximum allowed limit" in response.json()["detail"].lower()


def test_api_stt_transcribe_alias_endpoint(client: TestClient):
    """Ensure /api/stt/transcribe secondary alias endpoint also works."""
    wav = make_wav_bytes(0.5)
    files = {"audio_file": ("sample.wav", wav, "audio/wav")}
    response = client.post("/api/stt/transcribe", files=files)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


def test_api_transcribe_secret_leakage_prevention(client: TestClient):
    """Verify that neither success nor error responses ever leak sensitive credentials."""
    wav = make_wav_bytes(0.5)
    files = {"audio_file": ("sample.wav", wav, "audio/wav")}
    response = client.post("/api/transcribe", files=files)
    text = response.text
    assert "GNANI_API_KEY" not in text
    assert "api_key" not in text
    assert "X-API-Key-ID" not in text

