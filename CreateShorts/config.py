"""
Centralized constants for the AI Short-Video Generator pipeline.
Import from here instead of defining locally in individual modules.
"""
from typing import Final

# Script generation
WORDS_PER_MINUTE: Final[int] = 250
SECONDS_PER_MINUTE: Final[int] = 60

# Video rendering
VERTICAL_WIDTH: Final[int] = 1080
VERTICAL_HEIGHT: Final[int] = 1920
FPS: Final[int] = 30
AUDIO_BUFFER_SEC: Final[float] = 0.5
DEFAULT_BACKGROUND_VOLUME: Final[float] = 0.10

# SFX processing
SFX_MAX_DURATION_MS: Final[int] = 3000
SFX_TARGET_DBFS: Final[float] = -6.0
BEAT_DELAY_SECONDS: Final[dict] = {"none": 0.0, "short": 0.3, "long": 0.7}
