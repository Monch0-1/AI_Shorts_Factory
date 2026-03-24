import os
import yaml
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
from sqlmodel import Session, select, SQLModel
from CreateShorts.database import engine, init_db
from CreateShorts.Models.database_models import SFXLibrary
from CreateShorts.utils import get_project_root

class SFXLibraryManager:
    """
    Unified manager for SFX Library operations: Ingestion, Syncing, Listing, and Reseting.
    """
    
    def __init__(self, sfx_root_dir: str = "resources/sfx"):
        self.project_root = get_project_root()
        self.sfx_path = self.project_root / sfx_root_dir
        self.yaml_path = self.project_root / "CreateShorts" / "theme_media_resources.yml"

    def reset_database(self):
        """Drops and recreates all tables in the database."""
        print("--- Resetting Database ---")
        print("Dropping all tables...")
        SQLModel.metadata.drop_all(engine)
        print("Creating all tables with new schema...")
        SQLModel.metadata.create_all(engine)
        print("Database reset successful.")

    def bulk_ingest(self) -> Dict[str, int]:
        """
        Scans the SFX root directory and syncs all found audio files to the database.
        Expected structure: {root}/{category}/{intent_tag}/{filename}.mp3
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
                for tag_dir in category_dir.iterdir():
                    if not tag_dir.is_dir():
                        continue
                    
                    intent_tag = tag_dir.name
                    for file in tag_dir.iterdir():
                        if file.suffix.lower() in extensions:
                            relative_path = str(file.relative_to(self.project_root)).replace("\\", "/")
                            
                            existing = session.exec(
                                select(SFXLibrary).where(SFXLibrary.file_path == relative_path)
                            ).first()
                            
                            if existing:
                                skipped_count += 1
                                continue
                            
                            new_sfx = SFXLibrary(
                                category=category,
                                intent_tag=intent_tag,
                                sfx_name=file.stem.replace("_", " ").title(),
                                file_path=relative_path,
                                description=f"Auto-ingested {category}/{intent_tag} effect",
                                source="local"
                            )
                            session.add(new_sfx)
                            new_count += 1
            
            session.commit()
        
        print(f"✅ Added {new_count} new sound effects. Skipped {skipped_count} existing records.")
        return {"new": new_count, "skipped": skipped_count}

    def sync_to_yaml(self):
        """Updates the theme_media_resources.yml with the latest DB mapping."""
        if not self.yaml_path.exists():
            print(f"❌ YAML File not found: {self.yaml_path}")
            return

        new_mapping = defaultdict(set)
        with Session(engine) as session:
            statement = select(SFXLibrary.category, SFXLibrary.intent_tag)
            results = session.exec(statement).all()
            for category, intent_tag in results:
                new_mapping[category].add(intent_tag)

        final_mapping = {cat: sorted(list(tags)) for cat, tags in sorted(new_mapping.items())}

        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'resources' not in config:
                config['resources'] = {}
            config['resources']['sfx_audio'] = final_mapping

            with open(self.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, sort_keys=False, indent=2, allow_unicode=True)
            print("✅ SFX Mapping successfully synchronized from Database to YAML.")
        except Exception as e:
            print(f"❌ Error updating YAML: {e}")

    def full_sync(self):
        """Performs both bulk ingestion and YAML synchronization in one atomic task."""
        print("\n--- Starting Full SFX Library Sync ---")
        self.bulk_ingest()
        self.sync_to_yaml()
        print("--- Full Sync Complete ---\n")

    def list_library(self):
        """Prints all entries in the SFXLibrary database."""
        with Session(engine) as session:
            statement = select(SFXLibrary)
            results = session.exec(statement).all()
            print(f"\n--- SFX Library Status ({len(results)} entries) ---")
            for item in results:
                print(f"- {item.sfx_name} ({item.category}/{item.intent_tag}) | Count: {item.usage_count} | Path: {item.file_path}")
