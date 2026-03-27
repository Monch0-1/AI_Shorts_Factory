from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone


class SFXAssetTagLink(SQLModel, table=True):
    """Junction table for the N:M relationship between SFXAsset and SFXTag."""
    __tablename__ = "sfx_asset_tag_link"

    asset_id: Optional[int] = Field(default=None, foreign_key="sfx_asset.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="sfx_tag.id", primary_key=True)


class SFXTag(SQLModel, table=True):
    """A single descriptive trait tag (e.g., 'bonk', 'metallic', 'cartoon')."""
    __tablename__ = "sfx_tag"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    assets: List["SFXAsset"] = Relationship(back_populates="tags", link_model=SFXAssetTagLink)


class SFXAsset(SQLModel, table=True):
    """An audio asset in the SFX library, described by a category and N:M trait tags."""
    __tablename__ = "sfx_asset"

    id: Optional[int] = Field(default=None, primary_key=True)
    file_path: str = Field(unique=True)
    category: str = Field(index=True)          # e.g., 'horror', 'comedy', 'neutral'
    description: Optional[str] = None          # Natural language prompt used to generate this asset
    usage_count: int = Field(default=0)
    popularity_score: float = Field(default=0.0)
    source: str = Field(default="local")        # 'local' or 'eleven_labs'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None

    tags: List[SFXTag] = Relationship(back_populates="assets", link_model=SFXAssetTagLink)
