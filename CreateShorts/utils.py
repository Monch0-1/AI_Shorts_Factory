from pathlib import Path
from elevenlabs.types import VoiceSettings
from typing import Optional

def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    return Path(__file__).parent.parent

