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
@patch('os.path.exists')
@patch('os.makedirs')
def test_assemble_dialogue_v2_success(mock_makedirs, mock_exists, mock_composite, mock_audio_clip_class, mock_theme_config):
    # Setup mocks
    mock_exists.return_value = True # All paths exist
    
    mock_voice_clip = MagicMock()
    mock_voice_clip.set_start.return_value = mock_voice_clip
    
    mock_sfx_clip = MagicMock()
    mock_sfx_clip.set_start.return_value = mock_sfx_clip
    mock_sfx_clip.volumex.return_value = mock_sfx_clip
    
    # Return voice clip then SFX clip
    mock_audio_clip_class.side_effect = [mock_voice_clip, mock_sfx_clip]
    
    # Create ScriptDTO with one highlight
    highlight = HighlightDTO(type="funny", context="counter")
    segments = [
        SegmentDTO(speaker="Nina", line="Joke", audio_path="nina.mp3", duration=2.0, highlight=highlight)
    ]
    script = ScriptDTO(topic="Comedy", segments=segments)
    
    # Execute
    result = assemble_dialogue_v2(script, mock_theme_config, "output/master.mp3")
    
    # Assertions
    assert result == "output/master.mp3"
    assert mock_audio_clip_class.call_count == 2
    mock_audio_clip_class.assert_any_call("nina.mp3")
    mock_audio_clip_class.assert_any_call("laugh.mp3")
    
    mock_composite.assert_called_once()
    # Verify CompositeAudioClip was called with list of clips
    args, _ = mock_composite.call_args
    assert len(args[0]) == 2 # 1 voice + 1 sfx

@patch('CreateShorts.Data_Gen.create_audio.AudioFileClip')
@patch('os.path.exists')
def test_assemble_dialogue_v2_no_segments(mock_exists, mock_audio_clip_class, mock_theme_config):
    script = ScriptDTO(topic="Empty", segments=[])
    result = assemble_dialogue_v2(script, mock_theme_config, "output.mp3")
    assert result is None

@patch('CreateShorts.Data_Gen.create_audio.AudioFileClip')
@patch('os.path.exists')
def test_assemble_dialogue_v2_missing_audio_files(mock_exists, mock_audio_clip_class, mock_theme_config):
    mock_exists.return_value = False
    segments = [SegmentDTO(speaker="Nina", line="No audio", audio_path="missing.mp3")]
    script = ScriptDTO(topic="Test", segments=segments)
    
    result = assemble_dialogue_v2(script, mock_theme_config, "output.mp3")
    assert result is None
