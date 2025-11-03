
from dataclasses import dataclass
from typing import Optional

@dataclass
class ElevenLabsVoiceSettings:
    """Configuration for the ElevenLabs voice"""
    stability: Optional[float] = None
    similarity_boost: Optional[float] = None
    style: Optional[float] = None
    speed: Optional[float] = None
    use_speaker_boost: Optional[bool] = None