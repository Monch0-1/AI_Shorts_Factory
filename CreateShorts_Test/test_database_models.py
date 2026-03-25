"""
Tests for the remodeled database schema (RF1).
Uses an in-memory SQLite engine to avoid requiring a live Postgres connection.
"""
import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from CreateShorts.Models.database_models import SFXAsset, SFXTag, SFXAssetTagLink


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_sfx_asset_creation(session):
    """SFXAsset can be created with required fields and correct defaults."""
    asset = SFXAsset(file_path="resources/sfx/comedy/bonk/bonk_01.mp3", category="comedy")
    session.add(asset)
    session.commit()
    session.refresh(asset)

    assert asset.id is not None
    assert asset.category == "comedy"
    assert asset.usage_count == 0
    assert asset.popularity_score == 0.0
    assert asset.source == "local"
    assert asset.last_used is None


def test_sfx_tag_creation(session):
    """SFXTag can be created with a unique name."""
    tag = SFXTag(name="bonk")
    session.add(tag)
    session.commit()
    session.refresh(tag)

    assert tag.id is not None
    assert tag.name == "bonk"


def test_sfx_tag_uniqueness(session):
    """Inserting two SFXTags with the same name raises an integrity error."""
    from sqlalchemy.exc import IntegrityError

    session.add(SFXTag(name="cartoon"))
    session.commit()

    session.add(SFXTag(name="cartoon"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_asset_tag_link(session):
    """An SFXAsset can be linked to multiple SFXTags via the junction table."""
    asset = SFXAsset(file_path="resources/sfx/comedy/bonk/bonk_01.mp3", category="comedy")
    tag_bonk = SFXTag(name="bonk")
    tag_cartoon = SFXTag(name="cartoon")

    session.add_all([asset, tag_bonk, tag_cartoon])
    session.flush()

    session.add(SFXAssetTagLink(asset_id=asset.id, tag_id=tag_bonk.id))
    session.add(SFXAssetTagLink(asset_id=asset.id, tag_id=tag_cartoon.id))
    session.commit()

    # Query linked tags for the asset
    linked_tags = session.exec(
        select(SFXTag)
        .join(SFXAssetTagLink, SFXAssetTagLink.tag_id == SFXTag.id)
        .where(SFXAssetTagLink.asset_id == asset.id)
    ).all()

    tag_names = {t.name for t in linked_tags}
    assert tag_names == {"bonk", "cartoon"}


def test_multiple_assets_share_tag(session):
    """A single SFXTag can be linked to multiple assets (N:M)."""
    asset_a = SFXAsset(file_path="resources/sfx/comedy/bonk/bonk_01.mp3", category="comedy")
    asset_b = SFXAsset(file_path="resources/sfx/comedy/bonk/bonk_02.mp3", category="comedy")
    tag = SFXTag(name="fast")

    session.add_all([asset_a, asset_b, tag])
    session.flush()

    session.add(SFXAssetTagLink(asset_id=asset_a.id, tag_id=tag.id))
    session.add(SFXAssetTagLink(asset_id=asset_b.id, tag_id=tag.id))
    session.commit()

    linked_assets = session.exec(
        select(SFXAsset)
        .join(SFXAssetTagLink, SFXAssetTagLink.asset_id == SFXAsset.id)
        .where(SFXAssetTagLink.tag_id == tag.id)
    ).all()

    assert len(linked_assets) == 2


def test_asset_usage_tracking(session):
    """usage_count and last_used can be updated on an asset."""
    from datetime import datetime

    asset = SFXAsset(file_path="resources/sfx/horror/jump_scare/scare_01.mp3", category="horror")
    session.add(asset)
    session.commit()

    asset.usage_count += 1
    asset.last_used = datetime.utcnow()
    session.add(asset)
    session.commit()
    session.refresh(asset)

    assert asset.usage_count == 1
    assert asset.last_used is not None
