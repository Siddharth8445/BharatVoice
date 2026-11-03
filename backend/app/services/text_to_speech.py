
import io
import logging
import wave
from typing import Optional

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

WAV_MIME = "audio/wav"


def generate_mock_wav(duration_seconds: float = 0.5) -> bytes:
    """Generate a valid silent WAV file for mock mode."""
    sample_rate = 16000
    n_frames = int(sample_rate * duration_seconds)

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * n_frames)

    return buffer.getvalue()


def repair_streaming_wav(audio_bytes: bytes) -> bytes:
    """
    Repair WAV files returned by streaming TTS providers.

    Gnani may return 0xFFFFFFFF placeholders for the RIFF
    and data chunk sizes. Replace them with actual file sizes.
    """
    audio = bytearray(audio_bytes)

    if (
        len(audio) < 44
        or audio[0:4] != b"RIFF"
        or audio[8:12] != b"WAVE"
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gnani TTS returned invalid WAV audio data.",
        )

    # Repair RIFF chunk size.
    if audio[4:8] == b"\xff\xff\xff\xff":
        audio[4:8] = (len(audio) - 8).to_bytes(4, "little")

    # Repair data chunk size.
    data_position = audio.find(b"data", 12)

    if data_position != -1:
        size_position = data_position + 4

        if (
            size_position + 4 <= len(audio)
            and audio[size_position:size_position + 4]
            == b"\xff\xff\xff\xff"
        ):
            actual_data_size = len(audio) - (size_position + 4)
            audio[size_position:size_position + 4] = (
                actual_data_size.to_bytes(4, "little")
            )

    return bytes(audio)


class TextToSpeechService:
    """Convert Hindi text into spoken audio using Gnani Timbre."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.settings = settings or get_settings()
        self._http_client = http_client

    async def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> bytes:
        """Generate WAV audio from the supplied text."""

        if not text or not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text for synthesis cannot be empty.",
            )

        language = language or self.settings.GNANI_TTS_LANGUAGE
        voice = voice or self.settings.GNANI_TTS_VOICE
        speed = (
            speed
            if speed is not None
            else self.settings.GNANI_TTS_SPEED
        )

        # Mock mode.
        if self.settings.USE_MOCK_GNANI:
            logger.info("Gnani TTS mock mode: returning silent WAV.")
            return generate_mock_wav()

        # Validate API key.
        api_key = self.settings.GNANI_API_KEY

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gnani API key is required for real TTS mode.",
            )

        payload = {
            "text": text.strip(),
            "voice": voice,
            "model": self.settings.GNANI_TTS_MODEL,
            "language": language,
            "speed": speed,
            "audio_config": {
                "sample_rate": 48000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            },
        }

        headers = {
            "X-API-Key-ID": api_key.strip(),
            "Content-Type": "application/json",
        }

        timeout = self.settings.GNANI_TTS_TIMEOUT_SECONDS
        client = self._http_client or httpx.AsyncClient(
            timeout=timeout
        )

        try:
            response = await client.post(
                self.settings.GNANI_TTS_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=timeout,
            )

            if response.status_code != 200:
                logger.error(
                    "Gnani TTS error: status=%s, response=%s",
                    response.status_code,
                    response.text[:300],
                )

                if response.status_code in (401, 403):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Gnani TTS authentication failed.",
                    )

                if response.status_code == 429:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Gnani TTS rate limit exceeded.",
                    )

                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=(
                        "Gnani TTS returned status "
                        f"{response.status_code}."
                    ),
                )

            content_type = response.headers.get(
                "Content-Type", ""
            )
            content_type = (
                content_type.split(";")[0].strip().lower()
            )

            if content_type != WAV_MIME:
                logger.error(
                    "Unexpected Gnani TTS content type: %s",
                    content_type,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Gnani TTS response was not WAV audio.",
                )

            if not response.content:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Gnani TTS returned empty audio.",
                )

            audio_bytes = repair_streaming_wav(response.content)

            logger.info(
                "Gnani TTS successful: %s bytes generated.",
                len(audio_bytes),
            )

            return audio_bytes

        except HTTPException:
            raise

        except httpx.TimeoutException as exc:
            logger.error("Gnani TTS timeout: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Gnani TTS request timed out.",
            ) from exc

        except httpx.RequestError as exc:
            logger.error("Gnani TTS network error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Network error contacting Gnani TTS.",
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected Gnani TTS failure")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected failure during TTS synthesis.",
            ) from exc

        finally:
            if self._http_client is None:
                await client.aclose()


_tts_service: Optional[TextToSpeechService] = None


def get_text_to_speech_service() -> TextToSpeechService:
    """Return the shared TTS service instance."""
    global _tts_service

    if _tts_service is None:
        _tts_service = TextToSpeechService()

    return _tts_service

