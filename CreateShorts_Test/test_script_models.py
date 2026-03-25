"""
Tests for HighlightDTO expansion (RF2): category, desired_traits, beat_delay.
"""
import pytest
from CreateShorts.Models.script_models import HighlightDTO, SegmentDTO, ScriptDTO


def test_highlight_dto_defaults():
    """HighlightDTO has correct default values for all optional fields."""
    h = HighlightDTO(category="comedy")

    assert h.category == "comedy"
    assert h.desired_traits == []
    assert h.placement == "end"
    assert h.beat_delay == "none"
    assert h.offset_seconds == 0.0
    assert h.volume_modifier == 0.0
    assert h.resource_path is None


def test_highlight_dto_full_construction():
    """HighlightDTO accepts all fields correctly."""
    h = HighlightDTO(
        category="horror",
        desired_traits=["sharp", "metallic", "echo"],
        placement="start",
        beat_delay="long",
        offset_seconds=-0.2,
        volume_modifier=3.0,
        resource_path="resources/sfx/horror/jump_scare/scare_01.mp3"
    )

    assert h.category == "horror"
    assert h.desired_traits == ["sharp", "metallic", "echo"]
    assert h.placement == "start"
    assert h.beat_delay == "long"
    assert h.offset_seconds == -0.2
    assert h.volume_modifier == 3.0
    assert h.resource_path == "resources/sfx/horror/jump_scare/scare_01.mp3"


def test_highlight_dto_short_beat_delay():
    """beat_delay 'short' is accepted."""
    h = HighlightDTO(category="neutral", beat_delay="short")
    assert h.beat_delay == "short"


def test_segment_dto_with_highlight():
    """SegmentDTO correctly nests a HighlightDTO."""
    h = HighlightDTO(category="comedy", desired_traits=["bonk", "cartoon"])
    seg = SegmentDTO(speaker="Narrator", line="This is a test line.", highlight=h)

    assert seg.highlight is not None
    assert seg.highlight.category == "comedy"
    assert "bonk" in seg.highlight.desired_traits


def test_segment_dto_without_highlight():
    """SegmentDTO highlight is optional."""
    seg = SegmentDTO(speaker="Narrator", line="No SFX here.")
    assert seg.highlight is None


def test_script_dto_construction():
    """ScriptDTO holds a topic and list of SegmentDTOs."""
    segments = [
        SegmentDTO(speaker="A", line="Line one."),
        SegmentDTO(speaker="B", line="Line two.", highlight=HighlightDTO(
            category="comedy",
            desired_traits=["laugh", "silly"],
            beat_delay="short"
        ))
    ]
    script = ScriptDTO(topic="Test Topic", segments=segments)

    assert script.topic == "Test Topic"
    assert len(script.segments) == 2
    assert script.segments[1].highlight.desired_traits == ["laugh", "silly"]


def test_highlight_dto_old_fields_removed():
    """HighlightDTO no longer has 'type' or 'context' fields."""
    h = HighlightDTO(category="comedy")
    assert not hasattr(h, "type") or "type" not in h.model_fields
    assert not hasattr(h, "context") or "context" not in h.model_fields
