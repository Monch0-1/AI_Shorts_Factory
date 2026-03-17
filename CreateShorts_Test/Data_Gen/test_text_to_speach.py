import pytest
from unittest.mock import MagicMock, patch, mock_open
from CreateShorts.Data_Gen.text_to_speach import generate_script_audio_v2, get_elevenlabs_settings
from CreateShorts.Models.script_models import ScriptDTO, SegmentDTO
from CreateShorts.theme_config import ThemeConfig
from CreateShorts.Data_Gen.eleven_labs_voice_settings_config import ElevenLabsVoiceSettings
import os

@pytest.fixture
def mock_theme_config():
    voice_settings = ElevenLabsVoiceSettings(
        stability=0.5,
        similarity_boost=0.75,
        style=0.0,
        speed=1.0,
        use_speaker_boost=True
    )
    config = MagicMock(spec=ThemeConfig)
    config.voice_settings = voice_settings
    return config

def test_get_elevenlabs_settings_default():
    settings = get_elevenlabs_settings(None)
    assert settings.stability == 0.5
    assert settings.similarity_boost == 0.75
    assert settings.speed == 1.0

def test_get_elevenlabs_settings_custom():
    custom_data = ElevenLabsVoiceSettings(stability=0.8, similarity_boost=0.9)
    settings = get_elevenlabs_settings(custom_data)
    assert settings.stability == 0.8
    assert settings.similarity_boost == 0.9
    assert settings.speed == 1.0 # Default from the function

@patch('CreateShorts.Data_Gen.text_to_speach.AudioFileClip')
@patch('CreateShorts.Data_Gen.text_to_speach.client')
@patch('os.makedirs')
@patch('builtins.open', new_callable=mock_open)
def test_generate_script_audio_v2_success(mock_file, mock_makedirs, mock_client, mock_audio_clip_class, mock_theme_config):
    # Setup mocks
    mock_audio_generator = [b'audio_chunk_1', b'audio_chunk_2']
    mock_client.text_to_speech.convert.return_value = mock_audio_generator
    
    mock_audio_clip = mock_audio_clip_class.return_value.__enter__.return_value
    mock_audio_clip.duration = 5.5
    
    # Create ScriptDTO
    segments = [
        SegmentDTO(speaker="Nina", line="Hello world"),
        SegmentDTO(speaker="Tina", line="Hi there")
    ]
    script = ScriptDTO(topic="Test Topic", segments=segments)
    
    # Execute
    result_script = generate_script_audio_v2(script, mock_theme_config)
    
    # Assertions
    assert len(result_script.segments) == 2
    assert result_script.segments[0].duration == 5.5
    assert result_script.segments[0].audio_path is not None
    assert "Nina" in result_script.segments[0].audio_path or "seg_0" in result_script.segments[0].audio_path
    
    assert mock_client.text_to_speech.convert.call_count == 2
    assert mock_file.call_count == 2
    # Verify we wrote the combined chunks
    mock_file().write.assert_called_with(b'audio_chunk_1audio_chunk_2')

@patch('CreateShorts.Data_Gen.text_to_speach.client')
def test_generate_script_audio_v2_no_client(mock_client):
    # Set global client to None in the module scope for this test
    with patch('CreateShorts.Data_Gen.text_to_speach.client', None):
        script = ScriptDTO(topic="Test", segments=[])
        theme_config = MagicMock()
        result = generate_script_audio_v2(script, theme_config)
        assert result == script
