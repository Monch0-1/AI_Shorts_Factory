import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlmodel import Session, select
from CreateShorts.database import engine
from CreateShorts.Interfaces.interfaces import ISFXProvider
from CreateShorts.Models.database_models import SFXAsset, SFXTag, SFXAssetTagLink

logger = logging.getLogger(__name__)

QUALITY_GATE = 60.0          # Minimum score to accept a local asset
TRAIT_MATCH_THRESHOLD = 0.5  # Assets matching < 50% of requested traits are discarded

# Scoring weights (must sum to 100)
W_CATEGORY = 50.0
W_TRAITS = 40.0
W_VARIETY = 10.0


class LocalSFXProvider(ISFXProvider):
    """
    Selects SFX assets from the local database using a semantic scoring algorithm (RF3).

    Scoring:
      - Category Match (50%): Mandatory — asset category must equal requested category.
      - Trait Intersection (40%): matched_traits / requested_traits count.
        Assets below TRAIT_MATCH_THRESHOLD are discarded before scoring.
      - LRU / Variety (10%): Prefer less-recently and less-frequently used assets.

    Returns None if no asset scores >= QUALITY_GATE (60/100), signalling the
    coordinator to fall back to the AI provider.
    """

    def get_sfx(self, category: str, desired_traits: List[str], description: Optional[str] = None) -> Optional[str]:
        with Session(engine) as session:
            try:
                assets = session.exec(
                    select(SFXAsset).where(SFXAsset.category == category)
                ).all()

                if not assets:
                    logger.info(f"LocalSFXProvider: No assets found for category '{category}'")
                    return None

                best_asset = None
                best_score = -1.0

                for asset in assets:
                    score = self._score(asset, desired_traits, session)
                    if score > best_score:
                        best_score = score
                        best_asset = asset

                if best_asset is None or best_score < QUALITY_GATE:
                    logger.info(
                        f"LocalSFXProvider: Best score {best_score:.1f}/100 below gate "
                        f"({QUALITY_GATE}) for category='{category}', traits={desired_traits}. "
                        f"Triggering AI fallback."
                    )
                    return None

                # Commit usage tracking
                best_asset.usage_count += 1
                best_asset.last_used = datetime.now(timezone.utc)
                session.add(best_asset)
                session.commit()

                logger.info(
                    f"LocalSFXProvider: Selected '{best_asset.file_path}' "
                    f"(score={best_score:.1f}/100)"
                )
                return best_asset.file_path

            except Exception as e:
                logger.error(f"LocalSFXProvider: Query error: {e}")
                session.rollback()
                return None

    def _score(self, asset: SFXAsset, desired_traits: List[str], session: Session) -> float:
        """
        Scores an asset against the requested traits.
        Returns -1.0 if the asset is disqualified by the trait threshold.
        """
        # Fetch asset tags
        asset_tags = session.exec(
            select(SFXTag)
            .join(SFXAssetTagLink, SFXAssetTagLink.tag_id == SFXTag.id)
            .where(SFXAssetTagLink.asset_id == asset.id)
        ).all()
        asset_tag_names = {t.name.lower() for t in asset_tags}

        # Trait intersection score
        if not desired_traits:
            trait_ratio = 1.0
        else:
            requested = [t.lower() for t in desired_traits]
            matched = sum(1 for t in requested if t in asset_tag_names)
            trait_ratio = matched / len(requested)

        # Discard assets below trait match threshold
        if desired_traits and trait_ratio < TRAIT_MATCH_THRESHOLD:
            return -1.0

        trait_score = trait_ratio * W_TRAITS

        # Variety score: favour low usage_count and older last_used
        # Normalise usage_count with a soft cap at 20 uses
        usage_penalty = min(asset.usage_count / 20.0, 1.0)
        variety_score = (1.0 - usage_penalty) * W_VARIETY

        total = W_CATEGORY + trait_score + variety_score
        return round(total, 2)
