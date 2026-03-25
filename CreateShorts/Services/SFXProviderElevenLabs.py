import logging
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
from sqlmodel import Session, select
from elevenlabs.client import ElevenLabs
from CreateShorts.database import engine
from CreateShorts.Interfaces.interfaces import ISFXProvider
from CreateShorts.Models.database_models import SFXAsset, SFXTag, SFXAssetTagLink
from CreateShorts.Services.AssetProcessor import AssetProcessor
from CreateShorts.loadEnvData import load_env_data
from CreateShorts.utils import get_project_root

logger = logging.getLogger(__name__)

SFX_OUTPUT_DIR = "resources/sfx"
OUTPUT_FORMAT = "mp3_44100_128"


class ElevenLabsSFXProvider(ISFXProvider):
    """
    Generates SFX assets via the ElevenLabs Sound Generation API as a fallback (RF3).

    On success:
    - Runs AssetProcessor (normalize -6dB, cap 3s) on the result (RT1)
    - Saves the file locally under resources/sfx/{category}/generated/
    - Registers the asset in the DB and links the requested traits as tags (RT2)
    """

    def __init__(self):
        self._client: Optional[ElevenLabs] = load_env_data(ElevenLabs, "ELEVEN_API_KEY")
        self._processor = AssetProcessor()
        self._project_root = get_project_root()

    def get_sfx(self, category: str, desired_traits: List[str]) -> Optional[str]:
        if self._client is None:
            logger.error("ElevenLabsSFXProvider: ELEVEN_API_KEY not configured.")
            return None

        prompt = self._build_prompt(category, desired_traits)
        logger.info(f"ElevenLabsSFXProvider: Generating SFX for prompt: '{prompt}'")

        try:
            audio_generator = self._client.text_to_sound_effects.convert(
                text=prompt,
                duration_seconds=3.0,
                prompt_influence=0.5,
                output_format=OUTPUT_FORMAT,
            )
            audio_bytes = b"".join(chunk for chunk in audio_generator)

            if not audio_bytes:
                logger.error("ElevenLabsSFXProvider: API returned empty audio.")
                return None

            file_path = self._save_asset(audio_bytes, category)
            if not file_path:
                return None

            # Run AssetProcessor: normalize + cap
            abs_path = str(self._project_root / file_path)
            self._processor.process(abs_path)

            # Register in DB with requested traits (Self-Learning Cache)
            self._register_asset(file_path, category, desired_traits)

            logger.info(f"ElevenLabsSFXProvider: Saved and registered '{file_path}'")
            return file_path

        except Exception as e:
            logger.error(f"ElevenLabsSFXProvider: Generation failed: {e}")
            return None

    def _build_prompt(self, category: str, desired_traits: List[str]) -> str:
        """Combines category and traits into a descriptive sound prompt."""
        if desired_traits:
            return f"{category} sound effect: {', '.join(desired_traits)}"
        return f"{category} sound effect"

    def _save_asset(self, audio_bytes: bytes, category: str) -> Optional[str]:
        """Saves audio bytes to resources/sfx/{category}/generated/ and returns the relative path."""
        try:
            output_dir = self._project_root / SFX_OUTPUT_DIR / category / "generated"
            output_dir.mkdir(parents=True, exist_ok=True)

            file_name = f"gen_{uuid.uuid4().hex[:8]}.mp3"
            abs_path = output_dir / file_name
            abs_path.write_bytes(audio_bytes)

            relative_path = str(abs_path.relative_to(self._project_root)).replace("\\", "/")
            return relative_path

        except Exception as e:
            logger.error(f"ElevenLabsSFXProvider: Failed to save asset: {e}")
            return None

    def _register_asset(self, file_path: str, category: str, traits: List[str]):
        """Registers the generated asset in the DB and links trait tags (RT2)."""
        with Session(engine) as session:
            try:
                asset = SFXAsset(
                    file_path=file_path,
                    category=category,
                    source="eleven_labs",
                    created_at=datetime.now(timezone.utc)
                )
                session.add(asset)
                session.flush()

                for trait_name in traits:
                    tag = session.exec(
                        select(SFXTag).where(SFXTag.name == trait_name.lower())
                    ).first()
                    if not tag:
                        tag = SFXTag(name=trait_name.lower())
                        session.add(tag)
                        session.flush()

                    session.add(SFXAssetTagLink(asset_id=asset.id, tag_id=tag.id))

                session.commit()
            except Exception as e:
                logger.error(f"ElevenLabsSFXProvider: DB registration failed: {e}")
                session.rollback()
