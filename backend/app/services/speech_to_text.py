
import io
import logging
import uuid
import wave
from typing import Optional, Tuple

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.stt import TranscriptionResponse

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".webm"
}


def detect_audio_format(audio_bytes: bytes) -> Optional[str]:
    """Detect audio format using binary header signatures."""

    if len(audio_bytes) < 4:
        return None

    if (
        audio_bytes.startswith(b"RIFF")
        and len(audio_bytes) >= 12
        and audio_bytes[8:12] == b"WAVE"
    ):
        return "wav"

    if audio_bytes.startswith(b"ID3"):
        return "mp3"

    if audio_bytes[0] == 0xFF and (audio_bytes[1] & 0xE0) == 0xE0:
        return "mp3"

    if audio_bytes.startswith(b"OggS"):
        return "ogg"

    if audio_bytes.startswith(b"fLaC"):
        return "flac"

    if len(audio_bytes) >= 8 and audio_bytes[4:8] == b"ftyp":
        return "m4a"

    if audio_bytes.startswith(b"\xff\xf1") or audio_bytes.startswith(b"\xff\xf9"):
        return "aac"

    if audio_bytes.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"

    return None


def validate_audio_content(
    audio_bytes: bytes,
    filename: Optional[str] = None,
    max_file_size: int = 10485760,
    max_duration_seconds: int = 30,
) -> Tuple[str, str]:
    """Validate audio bytes and return detected format and MIME type."""

    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is empty. Please provide valid audio.",
        )

    if len(audio_bytes) > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Audio file size ({len(audio_bytes)} bytes) exceeds "
                f"the maximum limit of {max_file_size} bytes."
            ),
        )

    detected_format = detect_audio_format(audio_bytes)

    if not detected_format:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported or invalid audio format. "
                "Supported formats: WAV, MP3, OGG, FLAC, M4A, AAC, WebM."
            ),
        )

    if detected_format == "wav":
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                framerate = wf.getframerate()
                nframes = wf.getnframes()

                if framerate <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Corrupted WAV audio: invalid sample rate.",
                    )

                duration = nframes / float(framerate)

                if duration > max_duration_seconds:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Audio duration ({duration:.1f}s) exceeds "
                            f"maximum allowed limit of "
                            f"{max_duration_seconds} seconds."
                        ),
                    )

        except (wave.Error, EOFError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Corrupted or invalid WAV audio: {str(exc)}",
            )

    mime_map = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "webm": "audio/webm",
    }

    return detected_format, mime_map.get(
        detected_format, "application/octet-stream"
    )


class SpeechToTextService:
    """Transcribe audio using Gnani Prisma STT or local mock mode."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.settings = settings or get_settings()
        self._http_client = http_client

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: Optional[str] = "audio.wav",
        content_type: Optional[str] = None,
    ) -> TranscriptionResponse:
        """Transcribe audio using mock or real Gnani provider."""

        detected_format, mime_type = validate_audio_content(
            audio_bytes=audio_bytes,
            filename=filename,
            max_file_size=self.settings.MAX_AUDIO_FILE_SIZE_BYTES,
            max_duration_seconds=self.settings.MAX_AUDIO_DURATION_SECONDS,
        )

        effective_content_type = content_type or mime_type
        effective_filename = filename or f"audio.{detected_format}"

        # MOCK MODE
        if self.settings.USE_MOCK_GNANI:
            logger.info(
                "Gnani STT: Running in MOCK mode. Model: %s",
                self.settings.GNANI_STT_MODEL,
            )

            return TranscriptionResponse(
                success=True,
                transcript="Bhaiya, do kilo atta aur ek litre doodh bhej dena.",
                detected_language_code=(
                    self.settings.GNANI_STT_LANGUAGE_CODE
                    if self.settings.GNANI_STT_LANGUAGE_CODE != "indic-auto"
                    else "hi-IN"
                ),
                model=self.settings.GNANI_STT_MODEL,
                request_id=f"mock-stt-{uuid.uuid4().hex[:12]}",
                provider_mode="mock",
            )

        # REAL GNANI MODE
        api_key = self.settings.GNANI_API_KEY

        if not api_key or not api_key.strip():
            logger.error("Gnani STT: API key is not configured.")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gnani STT configuration error: API key is not configured.",
            )

        endpoint = self.settings.GNANI_STT_ENDPOINT

        headers = {
            "X-API-Key-ID": api_key.strip(),
        }

        files = {
            "audio_file": (
                effective_filename,
                audio_bytes,
                effective_content_type,
            ),
        }

        data = {
            "model": self.settings.GNANI_STT_MODEL,
            "language_code": self.settings.GNANI_STT_LANGUAGE_CODE,
        }

        logger.info(
            "Gnani STT: Calling upstream API. Model: %s, Language: %s",
            self.settings.GNANI_STT_MODEL,
            self.settings.GNANI_STT_LANGUAGE_CODE,
        )

        timeout = httpx.Timeout(30.0, connect=10.0)
        retries = 2
        last_exception = None

        for attempt in range(retries + 1):
            try:
                if self._http_client:
                    response = await self._http_client.post(
                        endpoint,
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=timeout,
                    )
                else:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.post(
                            endpoint,
                            headers=headers,
                            files=files,
                            data=data,
                        )

                # SUCCESS RESPONSE
                if response.status_code == status.HTTP_200_OK:
                    try:
                        resp_json = response.json()

                    except Exception:
                        logger.exception(
                            "Gnani STT: Failed to parse upstream JSON."
                        )

                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Gnani STT returned an invalid JSON response.",
                        )

                    if not isinstance(resp_json, dict):
                        logger.error(
                            "Gnani STT: Expected JSON object, received %s",
                            type(resp_json).__name__,
                        )

                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Gnani STT returned an unexpected response format.",
                        )

                    transcript = resp_json.get("transcript")

                    logger.info(
                        "Gnani STT diagnostic: status=%s, "
                        "response_keys=%s, transcript_length=%s",
                        response.status_code,
                        list(resp_json.keys()),
                        len(str(transcript or "")),
                    )

                    if transcript is None:
                        logger.error(
                            "Gnani STT: Transcript field missing. Response keys: %s",
                            list(resp_json.keys()),
                        )

                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Gnani STT response is missing transcript.",
                        )

                    if not isinstance(transcript, str):
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Gnani STT returned an invalid transcript format.",
                        )

                    if not transcript.strip():
                        logger.warning(
                            "Gnani STT: Provider returned an empty transcript."
                        )

                    return TranscriptionResponse(
                        success=bool(resp_json.get("success", True)),
                        transcript=transcript.strip(),
                        detected_language_code=resp_json.get(
                            "detected_language_code", "hi-IN"
                        ),
                        model=resp_json.get(
                            "model", self.settings.GNANI_STT_MODEL
                        ),
                        request_id=resp_json.get(
                            "request_id", str(uuid.uuid4())
                        ),
                        provider_mode="real",
                    )

                # AUTHENTICATION ERROR
                elif response.status_code in (
                    status.HTTP_401_UNAUTHORIZED,
                    status.HTTP_403_FORBIDDEN,
                ):
                    logger.error(
                        "Gnani STT: Authentication failed. Status: %d",
                        response.status_code,
                    )

                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=(
                            "Gnani STT authentication failed. "
                            "Please verify API key configuration."
                        ),
                    )

                # RATE LIMIT
                elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    logger.warning("Gnani STT: Rate limit reached.")

                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Gnani STT rate limit exceeded. Please try again later.",
                    )

                # RETRY TRANSIENT ERRORS
                elif response.status_code in (502, 503, 504) and attempt < retries:
                    logger.warning(
                        "Gnani STT: Temporary upstream error %d. Retrying...",
                        response.status_code,
                    )
                    continue

                # OTHER UPSTREAM ERRORS
                else:
                    logger.error(
                        "Gnani STT: Upstream error %d. Response: %s",
                        response.status_code,
                        response.text[:500],
                    )

                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=(
                            "Upstream speech-to-text service returned "
                            f"error code {response.status_code}."
                        ),
                    )

            except HTTPException:
                raise

            except (httpx.TimeoutException, TimeoutError) as exc:
                logger.warning(
                    "Gnani STT: Timeout on attempt %d: %s",
                    attempt + 1,
                    str(exc),
                )

                last_exception = exc

                if attempt < retries:
                    continue

                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Gnani STT request timed out. Please try again.",
                )

            except (httpx.ConnectError, httpx.NetworkError) as exc:
                logger.warning(
                    "Gnani STT: Network error on attempt %d: %s",
                    attempt + 1,
                    str(exc),
                )

                last_exception = exc

                if attempt < retries:
                    continue

                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Could not connect to the Gnani STT service.",
                )

            except Exception:
                logger.exception("Gnani STT: Unexpected transcription error.")

                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unexpected failure communicating with Gnani STT.",
                )

        if last_exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gnani STT request failed after retry attempts.",
            )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gnani STT request could not be completed.",
        )


# Singleton instance helper

_stt_service: Optional[SpeechToTextService] = None


def get_speech_to_text_service() -> SpeechToTextService:
    """Return the shared SpeechToTextService instance."""

    global _stt_service

    if _stt_service is None:
        _stt_service = SpeechToTextService()

    return _stt_service
