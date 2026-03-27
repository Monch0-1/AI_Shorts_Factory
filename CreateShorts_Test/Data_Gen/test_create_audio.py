import pytest
from unittest.mock import MagicMock, patch
from CreateShorts.Data_Gen.create_audio import assemble_dialogue_v2
from CreateShorts.Models.script_models import ScriptDTO, SegmentDTO, HighlightDTO

@pytest.fixture
def mock_theme_config():
    config = MagicMock()
    # Mock resources: h_type -> h_context -> [options]
    config.resources = {
        "funny": {
            "counter": [{"name": "laugh", "path": "laugh.mp3"}]
        }
    }
    return config

@patch('CreateShorts.Data_Gen.create_audio.AudioFileClip')
@patch('CreateShorts.Data_Gen.create_audio.CompositeAudioClip')
@patch('CreateShorts.Data_Gen.create_audio.SFXService')
@patch('os.path.exists')
@patch('os.makedirs')
def test_assemble_dialogue_v2_success(mock_makedirs, mock_exists, mock_sfx_service_class, mock_composite, mock_audio_clip_class, mock_theme_config):
    # Setup mocks
    mock_exists.return_value = True # All paths exist
    
    # Mock SFXService instance
    mock_sfx_service = mock_sfx_service_class.return_value
    mock_sfx_service.get_sfx_path.return_value = "mock_laugh.mp3"
    
    mock_voice_clip = MagicMock()
    mock_voice_clip.set_start.return_value = mock_voice_clip
    
    mock_sfx_clip = MagicMock()
    mock_sfx_clip.set_start.return_value = mock_sfx_clip
    mock_sfx_clip.volumex.return_value = mock_sfx_clip
    mock_sfx_clip.duration = 1.5
    
    # Return voice clip then SFX clip
    mock_audio_clip_class.side_effect = [mock_voice_clip, mock_sfx_clip]
    
    # Create ScriptDTO with one highlight using new fields
    highlight = HighlightDTO(
        category="funny",
        desired_traits=["counter"],
        placement="end",
        offset_seconds=0.1,
        volume_modifier=-2.0
    )
    segments = [
        SegmentDTO(speaker="Nina", line="Joke", audio_path="nina.mp3", duration=2.0, highlight=highlight)
    ]
    script = ScriptDTO(topic="Comedy", segments=segments)
    
    # Execute
    result = assemble_dialogue_v2(script, mock_theme_config, "output/master.mp3", include_sfx=True)
    
    # Assertions
    assert result == "output/master.mp3"
    assert mock_audio_clip_class.call_count == 2
    mock_audio_clip_class.assert_any_call("nina.mp3")
    mock_audio_clip_class.assert_any_call("mock_laugh.mp3")
    
    # Verify SFX placement/timing logic indirectly by checking clip calls
    # mock_sfx_clip.set_start was called with (2.0 + 0.1) = 2.1
    mock_sfx_clip.set_start.assert_called_with(2.1)
    
    mock_composite.assert_called_once()
    args, _ = mock_composite.call_args
    assert len(args[0]) == 2 # 1 voice + 1 sfx

@patch('CreateShorts.Data_Gen.create_audio.AudioFileClip')
@patch('CreateShorts.Data_Gen.create_audio.SFXService')
@patch('os.path.exists')
def test_assemble_dialogue_v2_include_sfx_false(mock_exists, mock_sfx_service_class, mock_audio_clip_class, mock_theme_config):
    mock_exists.return_value = True
    mock_sfx_service = mock_sfx_service_class.return_value
    
    highlight = HighlightDTO(category="funny", desired_traits=["counter"])
    segments = [
        SegmentDTO(speaker="Nina", line="Joke", audio_path="nina.mp3", duration=2.0, highlight=highlight)
    ]
    script = ScriptDTO(topic="Comedy", segments=segments)
    
    # Execute with include_sfx=False
    assemble_dialogue_v2(script, mock_theme_config, "output/master.mp3", include_sfx=False)
    
    # Verify SFX was NOT searched or loaded
    mock_sfx_service.get_sfx_path.assert_not_called()
    assert mock_audio_clip_class.call_count == 1
    mock_audio_clip_class.assert_called_once_with("nina.mp3")

@patch('CreateShorts.Data_Gen.create_audio.AudioFileClip')
@patch('os.path.exists')
def test_assemble_dialogue_v2_no_segments(mock_exists, mock_audio_clip_class, mock_theme_config):
    script = ScriptDTO(topic="Empty", segments=[])
    result = assemble_dialogue_v2(script, mock_theme_config, "output.mp3")
    assert result is None

@patch('CreateShorts.Data_Gen.create_audio.AudioFileClip')
@patch('CreateShorts.Data_Gen.create_audio.SFXService')
@patch('CreateShorts.Data_Gen.create_audio.os.path.exists')
def test_assemble_dialogue_v2_missing_audio_files(mock_exists, mock_sfx_service_class, mock_audio_clip_class, mock_theme_config):
    mock_exists.return_value = False
    segments = [SegmentDTO(speaker="Nina", line="No audio", audio_path="missing.mp3")]
    script = ScriptDTO(topic="Test", segments=segments)

    result = assemble_dialogue_v2(script, mock_theme_config, "output.mp3")
    assert result is None


@patch('CreateShorts.Data_Gen.create_audio.AudioFileClip')
@patch('CreateShorts.Data_Gen.create_audio.CompositeAudioClip')
@patch('CreateShorts.Data_Gen.create_audio.SFXService')
@patch('os.path.exists')
@patch('os.makedirs')
def test_rf4_end_placement_advances_by_sfx_duration_plus_beat_delay(
    mock_makedirs, mock_exists, mock_sfx_service_class, mock_composite, mock_audio_clip_class, mock_theme_config
):
    """RF4: end-placement SFX advances timeline by sfx_duration + beat_delay.
    Verified by checking set_start on the second segment's voice clip."""
    mock_exists.return_value = True

    mock_sfx_service = mock_sfx_service_class.return_value
    mock_sfx_service.get_sfx_path.return_value = "bonk.mp3"

    seg1_voice = MagicMock()
    seg1_voice.set_start.return_value = seg1_voice
    seg2_voice = MagicMock()
    seg2_voice.set_start.return_value = seg2_voice
    sfx_clip = MagicMock()
    sfx_clip.set_start.return_value = sfx_clip
    sfx_clip.volumex.return_value = sfx_clip
    sfx_clip.duration = 2.0  # SFX is 2 seconds long

    mock_audio_clip_class.side_effect = [seg1_voice, sfx_clip, seg2_voice]

    # Segment 1: 3s dialogue, end-placement SFX (2s), beat_delay="short" (0.3s)
    # Expected: seg2 starts at 3.0 + max(2.0 - 0.5, 0) + 0.3 = 3.0 + 1.5 + 0.3 = 4.8s
    highlight = HighlightDTO(category="comedy", desired_traits=["bonk"], placement="end", beat_delay="short")
    segments = [
        SegmentDTO(speaker="A", line="Line 1", audio_path="a.mp3", duration=3.0, highlight=highlight),
        SegmentDTO(speaker="B", line="Line 2", audio_path="b.mp3", duration=2.0),
    ]
    script = ScriptDTO(topic="RF4 Test", segments=segments)

    assemble_dialogue_v2(script, mock_theme_config, "output.mp3")

    seg2_voice.set_start.assert_called_with(4.8)


@patch('CreateShorts.Data_Gen.create_audio.AudioFileClip')
@patch('CreateShorts.Data_Gen.create_audio.CompositeAudioClip')
@patch('CreateShorts.Data_Gen.create_audio.SFXService')
@patch('os.path.exists')
@patch('os.makedirs')
def test_rf4_start_placement_advances_by_beat_delay_only(
    mock_makedirs, mock_exists, mock_sfx_service_class, mock_composite, mock_audio_clip_class, mock_theme_config
):
    """RF4: start-placement SFX plays simultaneously — only beat_delay advances the timeline."""
    mock_exists.return_value = True

    mock_sfx_service = mock_sfx_service_class.return_value
    mock_sfx_service.get_sfx_path.return_value = "whoosh.mp3"

    seg1_voice = MagicMock()
    seg1_voice.set_start.return_value = seg1_voice
    seg2_voice = MagicMock()
    seg2_voice.set_start.return_value = seg2_voice
    sfx_clip = MagicMock()
    sfx_clip.set_start.return_value = sfx_clip
    sfx_clip.volumex.return_value = sfx_clip
    sfx_clip.duration = 2.0

    mock_audio_clip_class.side_effect = [seg1_voice, sfx_clip, seg2_voice]

    # Segment 1: 3s dialogue, start-placement SFX, beat_delay="none" (0.0s)
    # Expected: seg2 starts at 3.0 (seg1 only) — sfx_duration NOT counted
    highlight = HighlightDTO(category="comedy", desired_traits=["whoosh"], placement="start", beat_delay="none")
    segments = [
        SegmentDTO(speaker="A", line="Line 1", audio_path="a.mp3", duration=3.0, highlight=highlight),
        SegmentDTO(speaker="B", line="Line 2", audio_path="b.mp3", duration=2.0),
    ]
    script = ScriptDTO(topic="RF4 Start Test", segments=segments)

    assemble_dialogue_v2(script, mock_theme_config, "output.mp3")

    seg2_voice.set_start.assert_called_with(3.0)
