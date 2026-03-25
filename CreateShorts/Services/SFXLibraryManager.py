import os
import yaml
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
from sqlmodel import Session, select, SQLModel
from CreateShorts.database import engine, init_db
from CreateShorts.Models.database_models import SFXAsset, SFXTag, SFXAssetTagLink
from CreateShorts.Services.AssetProcessor import AssetProcessor
from CreateShorts.utils import get_project_root


class SFXLibraryManager:
    """
    Unified manager for SFX Library operations: Ingestion, Syncing, Listing, and Resetting.

    Folder convention: {sfx_root}/{category}/{primary_trait}/{filename}.mp3
    - category  → SFXAsset.category
    - primary_trait folder name → first SFXTag linked to the asset
    Phase 3 (AssetProcessor) will add normalization (-6dB, 3s cap) to bulk_ingest.
    """

    def __init__(self, sfx_root_dir: str = "resources/sfx"):
        self.project_root = get_project_root()
        self.sfx_path = self.project_root / sfx_root_dir
        self.yaml_path = self.project_root / "CreateShorts" / "theme_media_resources.yml"
        self._processor = AssetProcessor()

    def reset_database(self):
        """Drops and recreates all tables in the database."""
        print("--- Resetting Database ---")
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        print("Database reset successful.")

    def _get_or_create_tag(self, session: Session, tag_name: str) -> SFXTag:
        """Returns an existing SFXTag by name or creates a new one."""
        tag = session.exec(select(SFXTag).where(SFXTag.name == tag_name)).first()
        if not tag:
            tag = SFXTag(name=tag_name)
            session.add(tag)
            session.flush()  # Ensure tag gets its id before linking
        return tag

    def bulk_ingest(self) -> Dict[str, int]:
        """
        Scans the SFX root directory and syncs all found audio files to the database.
        Expected structure: {root}/{category}/{primary_trait}/{filename}.mp3

        The primary_trait folder name is registered as the asset's first tag.
        Phase 3 will call AssetProcessor here for normalization and duration capping.
        """
        init_db()
        if not self.sfx_path.exists():
            print(f"❌ SFX Directory not found: {self.sfx_path}")
            return {"new": 0, "skipped": 0}

        extensions = [".mp3", ".wav", ".ogg"]
        new_count = 0
        skipped_count = 0

        with Session(engine) as session:
            for category_dir in self.sfx_path.iterdir():
                if not category_dir.is_dir():
                    continue

                category = category_dir.name
                for trait_dir in category_dir.iterdir():
                    if not trait_dir.is_dir():
                        continue

                    primary_trait = trait_dir.name
                    for file in trait_dir.iterdir():
                        if file.suffix.lower() not in extensions:
                            continue

                        relative_path = str(file.relative_to(self.project_root)).replace("\\", "/")

                        existing = session.exec(
                            select(SFXAsset).where(SFXAsset.file_path == relative_path)
                        ).first()

                        if existing:
                            skipped_count += 1
                            continue

                        # Pre-process: normalize -6dB, cap 3s (RT1)
                        self._processor.process(str(file))

                        # Create asset
                        asset = SFXAsset(
                            file_path=relative_path,
                            category=category,
                            source="local"
                        )
                        session.add(asset)
                        session.flush()  # Ensure asset gets its id

                        # Link primary trait tag
                        tag = self._get_or_create_tag(session, primary_trait)
                        link = SFXAssetTagLink(asset_id=asset.id, tag_id=tag.id)
                        session.add(link)

                        new_count += 1

            session.commit()

        print(f"✅ Added {new_count} new assets. Skipped {skipped_count} existing records.")
        return {"new": new_count, "skipped": skipped_count}

    def sync_to_yaml(self):
        """
        Updates the global sfx_audio trait catalog in theme_media_resources.yml
        from the current database state (category → list of unique tag names).
        """
        if not self.yaml_path.exists():
            print(f"❌ YAML File not found: {self.yaml_path}")
            return

        new_mapping = defaultdict(set)
        with Session(engine) as session:
            assets = session.exec(select(SFXAsset)).all()
            for asset in assets:
                # Re-fetch with relationship loaded
                asset_tags = session.exec(
                    select(SFXTag)
                    .join(SFXAssetTagLink, SFXAssetTagLink.tag_id == SFXTag.id)
                    .where(SFXAssetTagLink.asset_id == asset.id)
                ).all()
                for tag in asset_tags:
                    new_mapping[asset.category].add(tag.name)

        final_mapping = {cat: sorted(list(tags)) for cat, tags in sorted(new_mapping.items())}

        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if 'resources' not in config:
                config['resources'] = {}
            config['resources']['sfx_audio'] = final_mapping

            with open(self.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, sort_keys=False, indent=2, allow_unicode=True)
            print("✅ SFX trait catalog synchronized from Database to YAML.")
        except Exception as e:
            print(f"❌ Error updating YAML: {e}")

    def full_sync(self):
        """Performs bulk ingestion and YAML sync in one step."""
        print("\n--- Starting Full SFX Library Sync ---")
        self.bulk_ingest()
        self.sync_to_yaml()
        print("--- Full Sync Complete ---\n")

    def list_library(self):
        """Prints all assets in the SFXAsset database with their tags."""
        with Session(engine) as session:
            assets = session.exec(select(SFXAsset)).all()
            print(f"\n--- SFX Library Status ({len(assets)} assets) ---")
            for asset in assets:
                asset_tags = session.exec(
                    select(SFXTag)
                    .join(SFXAssetTagLink, SFXAssetTagLink.tag_id == SFXTag.id)
                    .where(SFXAssetTagLink.asset_id == asset.id)
                ).all()
                tag_names = ", ".join(t.name for t in asset_tags) or "no tags"
                print(f"- [{asset.category}] {asset.file_path} | Tags: {tag_names} | Uses: {asset.usage_count}")
