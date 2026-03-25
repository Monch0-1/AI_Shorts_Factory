"""
Tests for LocalSFXProvider semantic scoring (RF3).
Uses an in-memory SQLite DB — no live Postgres required.
"""
import pytest
from unittest.mock import patch
from sqlmodel import SQLModel, Session, create_engine, select
from CreateShorts.Models.database_models import SFXAsset, SFXTag, SFXAssetTagLink
from CreateShorts.Services.SFXProviderLocal import LocalSFXProvider, QUALITY_GATE


@pytest.fixture(name="engine_fixture")
def engine_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="provider")
def provider_fixture(engine_fixture):
    provider = LocalSFXProvider()
    # Patch the engine used inside the provider
    with patch("CreateShorts.Services.SFXProviderLocal.engine", engine_fixture):
        yield provider, engine_fixture


def _add_asset_with_tags(session, file_path, category, tags):
    asset = SFXAsset(file_path=file_path, category=category)
    session.add(asset)
    session.flush()
    for tag_name in tags:
        tag = session.exec(select(SFXTag).where(SFXTag.name == tag_name)).first()
        if not tag:
            tag = SFXTag(name=tag_name)
            session.add(tag)
            session.flush()
        session.add(SFXAssetTagLink(asset_id=asset.id, tag_id=tag.id))
    session.commit()
    return asset


def test_high_trait_match_accepted(provider):
    """Asset with 3/5 trait match (~74/100) should be accepted (above quality gate)."""
    prov, eng = provider
    with Session(eng) as session:
        _add_asset_with_tags(session, "sfx/comedy/bonk/a.mp3", "comedy",
                             ["bonk", "cartoon", "fast", "silly"])

    result = prov.get_sfx("comedy", ["bonk", "cartoon", "fast", "squeaky", "silly"])
    assert result == "sfx/comedy/bonk/a.mp3"


def test_low_trait_match_rejected(provider):
    """Asset with 1/5 trait match (20%) should be rejected — below 50% threshold."""
    prov, eng = provider
    with Session(eng) as session:
        _add_asset_with_tags(session, "sfx/comedy/bonk/a.mp3", "comedy", ["laugh"])

    result = prov.get_sfx("comedy", ["bonk", "cartoon", "fast", "squeaky", "silly"])
    assert result is None


def test_no_assets_returns_none(provider):
    """Returns None when no assets exist for the requested category."""
    prov, eng = provider
    result = prov.get_sfx("horror", ["sharp", "sudden"])
    assert result is None


def test_wrong_category_not_selected(provider):
    """Assets from a different category are not returned."""
    prov, eng = provider
    with Session(eng) as session:
        _add_asset_with_tags(session, "sfx/comedy/bonk/a.mp3", "comedy",
                             ["bonk", "cartoon", "fast"])

    result = prov.get_sfx("horror", ["bonk", "cartoon", "fast"])
    assert result is None


def test_best_scoring_asset_selected(provider):
    """When multiple assets exist, the one with the higher trait match is selected."""
    prov, eng = provider
    with Session(eng) as session:
        _add_asset_with_tags(session, "sfx/comedy/weak.mp3", "comedy", ["laugh"])
        _add_asset_with_tags(session, "sfx/comedy/strong.mp3", "comedy",
                             ["bonk", "cartoon", "fast"])

    result = prov.get_sfx("comedy", ["bonk", "cartoon", "fast"])
    assert result == "sfx/comedy/strong.mp3"


def test_empty_traits_uses_category_only(provider):
    """With no desired_traits, any asset in the category scores at Category(50) + Variety(10) = 60."""
    prov, eng = provider
    with Session(eng) as session:
        _add_asset_with_tags(session, "sfx/neutral/ding/a.mp3", "neutral", ["clean"])

    result = prov.get_sfx("neutral", [])
    assert result == "sfx/neutral/ding/a.mp3"
