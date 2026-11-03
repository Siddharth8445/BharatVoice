import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.schemas.stt import TranscriptionResponse
from app.services.speech_to_text import SpeechToTextService, get_speech_to_text_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Transcription"])


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe customer voice audio into text",
    description="Accepts multipart audio file, validates audio format/duration/size, and returns transcription via Gnani Prisma STT (or local mock).",
)
@router.post(
    "/stt/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Uploaded audio file (WAV, MP3, OGG, FLAC, M4A, AAC, WebM)"),
    stt_service: SpeechToTextService = Depends(get_speech_to_text_service),
) -> TranscriptionResponse:
    """Transcribe uploaded multipart audio file."""
    try:
        audio_bytes = await audio_file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded audio file: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded audio file stream.",
        )
    finally:
        await audio_file.close()

    return await stt_service.transcribe(
        audio_bytes=audio_bytes,
        filename=audio_file.filename,
        content_type=audio_file.content_type,
    )
