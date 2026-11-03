from typing import Optional
from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """Response model for speech-to-text audio transcription."""
    success: bool = Field(..., description="Whether the transcription was successful")
    transcript: str = Field(..., description="Transcribed text from the audio")
    detected_language_code: Optional[str] = Field(
        None, description="Language code detected by STT (e.g., 'hi-IN')"
    )
    model: str = Field(..., description="STT model identifier used")
    request_id: Optional[str] = Field(
        None, description="Request ID from Gnani provider or mock generator"
    )
    provider_mode: str = Field(
        ..., description="Execution mode: 'real' (live Gnani API) or 'mock' (local mock)"
    )
