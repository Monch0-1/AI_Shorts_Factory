from pydantic import BaseModel
from typing import List, Optional

class HighlightDTO(BaseModel):
    type: str
    context: str
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