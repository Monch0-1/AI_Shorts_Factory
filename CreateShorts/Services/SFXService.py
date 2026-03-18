import random
import logging
from typing import Optional, List
from datetime import datetime
from sqlmodel import Session, select
from CreateShorts.database import engine
from CreateShorts.Models.database_models import SFXLibrary

# Configure logging for SFX Service
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SFXService:
    def __init__(self, session: Optional[Session] = None):
        """
        Initializes the SFXService.
        :param session: Optional existing session (for transactions).
        """
        self._provided_session = session

    def _get_session(self) -> Session:
        """Returns the provided session or creates a new one from the engine."""
        if self._provided_session:
            return self._provided_session
        return Session(engine)

    def get_sfx_path(self, category: str, intent_tag: str) -> Optional[str]:
        """
        Queries the database for an SFX matching category and intent_tag.
        If found, updates its tracking fields and returns the file_path.
        
        :param category: The SFX category (e.g., 'horror', 'comedy')
        :param intent_tag: The specific intent (e.g., 'jump_scare', 'laugh')
        :return: Path to the audio file, or None if no matching resource exists.
        """
        session = self._get_session()
        try:
            # Query for all matches
            statement = select(SFXLibrary).where(
                SFXLibrary.category == category,
                SFXLibrary.intent_tag == intent_tag
            )
            results = session.exec(statement).all()

            if not results:
                logger.warning(
                    f"--- SFX MISSING ---\n"
                    f"Category: {category}, Tag: {intent_tag}\n"
                    f"No local resource found in SFXLibrary. "
                    f"Planned future improvement: Trigger ElevenLabs SFX API."
                )
                return None

            # Selection Strategy: Random for now
            selected_sfx = random.choice(results)

            # Update usage tracking
            selected_sfx.usage_count += 1
            selected_sfx.last_used = datetime.utcnow()
            
            session.add(selected_sfx)
            session.commit()
            session.refresh(selected_sfx)

            logger.info(f"Selected SFX: '{selected_sfx.sfx_name}' from {selected_sfx.file_path}")
            return selected_sfx.file_path

        except Exception as e:
            logger.error(f"Error querying SFXLibrary: {e}")
            session.rollback()
            return None
        finally:
            # Only close if we created the session ourselves
            if not self._provided_session:
                session.close()

    def sync_yaml_to_db(self, theme_manager):
        """
        Future utility: Check if all tags in theme_media_resources.yml 
        have at least one file in the SFXLibrary database.
        """
        sfx_mapping = theme_manager.get_sfx_mapping()
        missing_count = 0
        
        logger.info("--- SFX DB Sync Status ---")
        for category, tags in sfx_mapping.items():
            for tag in tags:
                with Session(engine) as session:
                    exists = session.exec(
                        select(SFXLibrary).where(
                            SFXLibrary.category == category, 
                            SFXLibrary.intent_tag == tag
                        )
                    ).first()
                    
                    if not exists:
                        logger.warning(f"DB Sync Alert: Category '{category}', Tag '{tag}' has NO files in database.")
                        missing_count += 1
        
        if missing_count == 0:
            logger.info("All YAML tags are fully synchronized with the database.")
        else:
            logger.info(f"Sync Check complete: {missing_count} tags are missing local files.")
