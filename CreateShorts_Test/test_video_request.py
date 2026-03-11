import pytest
from CreateShorts.Models.video_models import VideoRequest, VideoOptions

def test_video_request_defaults():
    """Test that VideoRequest initializes with correct default values in nested options."""
    request = VideoRequest(topic="Test Topic")
    
    assert request.topic == "Test Topic"
    assert request.theme == "default"
    assert request.is_monologue is False
    assert request.context_story == ""
    
    # Check options
    assert isinstance(request.options, VideoOptions)
    assert request.options.duration_seconds == 60
    assert request.options.use_script_template is False
    assert request.options.enable_refiner is False
    assert request.options.video_index is None

def test_video_request_custom_values():
    """Test that VideoRequest correctly stores custom values in nested options."""
    options = VideoOptions(
        duration_seconds=120,
        video_index=5,
        enable_refiner=True,
        use_script_template=True
    )
    request = VideoRequest(
        topic="Custom Topic",
        theme="horror",
        is_monologue=True,
        context_story="Scary story",
        options=options
    )
    
    assert request.topic == "Custom Topic"
    assert request.theme == "horror"
    assert request.is_monologue is True
    assert request.context_story == "Scary story"
    
    assert request.options.duration_seconds == 120
    assert request.options.video_index == 5
    assert request.options.enable_refiner is True
    assert request.options.use_script_template is True

def test_video_request_from_dict_nested():
    """Test that VideoRequest.from_dict correctly parses a nested dictionary."""
    data = {
        "topic": "Nested Topic",
        "theme": "nature",
        "options": {
            "duration_seconds": 30,
            "enable_refiner": True,
            "use_script_template": True
        }
    }
    
    request = VideoRequest.from_dict(data)
    
    assert request.topic == "Nested Topic"
    assert request.theme == "nature"
    assert request.options.duration_seconds == 30
    assert request.options.enable_refiner is True
    assert request.options.use_script_template is True

def test_video_request_from_dict_flat_compat():
    """Test that VideoRequest.from_dict still works with flat dictionaries for compatibility."""
    data = {
        "topic": "Flat Topic",
        "duration_seconds": 45,
        "enable_refiner": False,
        "use_template": True  # Testing legacy name mapping
    }
    
    request = VideoRequest.from_dict(data)
    
    assert request.topic == "Flat Topic"
    assert request.options.duration_seconds == 45
    assert request.options.enable_refiner is False
    assert request.options.use_script_template is True

def test_video_request_from_dict_empty():
    """Test that VideoRequest.from_dict handles empty dictionaries gracefully."""
    request = VideoRequest.from_dict({})
    
    assert request.topic == "Untitled"
    assert request.options.duration_seconds == 60
    assert request.options.enable_refiner is False
