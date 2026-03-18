import pytest
from CreateShorts.theme_config import ThemeManager

def test_get_all_available_tags():
    """
    Verifies that ThemeManager correctly flattens the global resources 
    to extract unique tags.
    """
    manager = ThemeManager()
    tags = manager.get_all_available_tags()
    
    # Based on the current theme_media_resources.yml:
    # horror: jump_scare, reveal
    # comedy: punchline, laugh
    # neutral: transition
    
    expected_tags = ["jump_scare", "laugh", "punchline", "reveal", "transition"]
    
    print(f"\nAvailable tags found: {tags}")
    
    for tag in expected_tags:
        assert tag in tags, f"Tag '{tag}' should be in the available tags list"
    
    assert len(tags) == len(expected_tags), "The number of tags found does not match expected"

def test_get_sfx_mapping():
    """
    Verifies that get_sfx_mapping returns the correct dictionary.
    """
    manager = ThemeManager()
    mapping = manager.get_sfx_mapping()
    
    assert "horror" in mapping
    assert "comedy" in mapping
    assert "neutral" in mapping
    assert mapping["horror"] == ["jump_scare", "reveal"]
    assert mapping["comedy"] == ["punchline", "laugh"]
    assert mapping["neutral"] == ["transition"]

def test_global_resources_loaded_correctly():
    """
    Verifies that the global resources dictionary is loaded as expected.
    """
    manager = ThemeManager()
    sfx_audio = manager.global_resources.get('sfx_audio', {})
    
    assert "horror" in sfx_audio
    assert "comedy" in sfx_audio
    assert "neutral" in sfx_audio
    
    assert "jump_scare" in sfx_audio["horror"]
    assert "laugh" in sfx_audio["comedy"]
