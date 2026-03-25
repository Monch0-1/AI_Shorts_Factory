import pytest
from CreateShorts.theme_config import ThemeManager


def test_get_all_available_tags():
    """
    Verifies that ThemeManager correctly flattens the global sfx_audio trait catalog.
    """
    manager = ThemeManager()
    tags = manager.get_all_available_tags()

    # Spot-check representative traits from each category
    expected_traits = ["bonk", "laugh", "sharp", "eerie", "clean", "soft"]

    print(f"\nAvailable traits found: {tags}")

    for trait in expected_traits:
        assert trait in tags, f"Trait '{trait}' should be in the available tags list"

    assert len(tags) > 0


def test_get_sfx_mapping():
    """
    Verifies that get_sfx_mapping returns the correct category structure.
    """
    manager = ThemeManager()
    mapping = manager.get_sfx_mapping()

    assert "horror" in mapping
    assert "comedy" in mapping
    assert "neutral" in mapping

    # Verify trait content per category
    assert "bonk" in mapping["comedy"]
    assert "sharp" in mapping["horror"]
    assert "clean" in mapping["neutral"]

    # Verify structure: each category maps to a non-empty list
    for category, traits in mapping.items():
        assert isinstance(traits, list), f"Category '{category}' should map to a list"
        assert len(traits) > 0, f"Category '{category}' should have at least one trait"


def test_global_resources_loaded_correctly():
    """
    Verifies that the global sfx_audio trait catalog is loaded with all three categories.
    """
    manager = ThemeManager()
    sfx_audio = manager.global_resources.get('sfx_audio', {})

    assert "horror" in sfx_audio
    assert "comedy" in sfx_audio
    assert "neutral" in sfx_audio

    assert "eerie" in sfx_audio["horror"]
    assert "laugh" in sfx_audio["comedy"]
    assert "subtle" in sfx_audio["neutral"]
