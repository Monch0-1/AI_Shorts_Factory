import logging
from typing import Optional, List
from CreateShorts.Interfaces.interfaces import ISFXProvider
from CreateShorts.Services.SFXProviderLocal import LocalSFXProvider
from CreateShorts.Services.SFXProviderElevenLabs import ElevenLabsSFXProvider
from CreateShorts.theme_config import ThemeManager
from sqlmodel import Session, select
from CreateShorts.database import engine
from CreateShorts.Models.database_models import SFXAsset

logger = logging.getLogger(__name__)


class SFXService:
    """
    Coordinator for SFX asset selection (RF3).

    Selection flow:
      1. LocalSFXProvider  — semantic scoring against the local DB.
         Accepts if score >= 60/100. Returns None if below threshold.
      2. ElevenLabsSFXProvider — AI generation fallback.
         Saves result locally and auto-tags it (Self-Learning Cache, RT2).
      3. If both fail, logs a warning and returns None.
    """

    def __init__(
        self,
        local_provider: Optional[ISFXProvider] = None,
        ai_provider: Optional[ISFXProvider] = None,
    ):
        self._local = local_provider or LocalSFXProvider()
        self._ai = ai_provider or ElevenLabsSFXProvider()

    def get_sfx_path(self, category: str, desired_traits: List[str]) -> Optional[str]:
        """
        Returns a file path for the best matching SFX asset.

        :param category: Primary SFX category (e.g., 'comedy', 'horror', 'neutral')
        :param desired_traits: Descriptive trait strings (e.g., ['bonk', 'cartoon'])
        :return: File path or None if no suitable asset could be found or generated.
        """
        # 1. Try local
        path = self._local.get_sfx(category, desired_traits)
        if path:
            return path

        # 2. Fallback to AI generation
        logger.info(
            f"SFXService: Local provider returned None for category='{category}', "
            f"traits={desired_traits}. Trying ElevenLabs."
        )
        path = self._ai.get_sfx(category, desired_traits)
        if path:
            return path

        logger.warning(
            f"SFXService: All providers failed for category='{category}', "
            f"traits={desired_traits}. No SFX will be applied."
        )
        return None

    def sync_yaml_to_db(self, theme_manager: ThemeManager):
        """
        Checks that all categories in the trait catalog have at least one local asset.
        """
        sfx_mapping = theme_manager.get_sfx_mapping()
        missing_count = 0

        logger.info("--- SFX DB Sync Status ---")
        for category in sfx_mapping.keys():
            with Session(engine) as session:
                exists = session.exec(
                    select(SFXAsset).where(SFXAsset.category == category)
                ).first()
                if not exists:
                    logger.warning(f"DB Sync: Category '{category}' has NO assets in database.")
                    missing_count += 1

        if missing_count == 0:
            logger.info("All categories are present in the database.")
        else:
            logger.info(f"Sync check complete: {missing_count} categories missing local assets.")
