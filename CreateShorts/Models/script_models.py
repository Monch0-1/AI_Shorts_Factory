from pydantic import BaseModel
from typing import List, Optional

class HighlightDTO(BaseModel):
    type: str
    context: str
    placement: str = "end"
    offset_seconds: float = 0.0
    volume_modifier: float = 0.0
    resource_path: Optional[str] = None

class SegmentDTO(BaseModel):
    speaker: str
    line: str
    highlight: Optional[HighlightDTO] = None
    audio_path: Optional[str] = None
    duration: float = 0.0

class ScriptDTO(BaseModel):
    topic: str
    segments: List[SegmentDTO]