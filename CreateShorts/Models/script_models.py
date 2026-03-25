from pydantic import BaseModel
from typing import List, Optional


class HighlightDTO(BaseModel):
    category: str                               # SFX category: 'comedy', 'horror', 'neutral'
    desired_traits: List[str] = []              # Descriptive traits: ['bonk', 'cartoon', 'fast']
    placement: str = "end"                      # 'start' or 'end' of the segment
    beat_delay: str = "none"                    # Pause after SFX: 'none', 'short' (0.3s), 'long' (0.7s)
    offset_seconds: float = 0.0                 # Fine-tune trigger: negative=overlap, positive=delay
    volume_modifier: float = 0.0               # dB adjustment for final mix
    resource_path: Optional[str] = None        # Resolved after SFX selection


class SegmentDTO(BaseModel):
    speaker: str
    line: str
    highlight: Optional[HighlightDTO] = None
    audio_path: Optional[str] = None
    duration: float = 0.0


class ScriptDTO(BaseModel):
    topic: str
    segments: List[SegmentDTO]
