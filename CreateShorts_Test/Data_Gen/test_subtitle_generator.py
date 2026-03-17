import pytest
from unittest.mock import MagicMock, patch
from CreateShorts.Data_Gen.subtitle_generator import SubtitleGenerator, SubtitleConfig
from CreateShorts.Models.script_models import ScriptDTO, SegmentDTO

def test_subtitle_config_defaults():
    config = SubtitleConfig()
    assert config.fontsize == 150
    assert config.color == 'white'

def test_optimize_text():
    generator = SubtitleGenerator()
    # Short text
    assert generator._optimize_text("Hello world") == "Hello world"
    # Long text (more than 6 words)
    long_text = "This is a very long sentence that needs breaking"
    optimized = generator._optimize_text(long_text)
    assert "\n" in optimized
    assert optimized.replace("\n", " ") == long_text

@patch('CreateShorts.Data_Gen.subtitle_generator.Image.new')
@patch('CreateShorts.Data_Gen.subtitle_generator.ImageDraw.Draw')
@patch('CreateShorts.Data_Gen.subtitle_generator.tempfile.NamedTemporaryFile')
def test_create_text_image(mock_temp, mock_draw, mock_image_new):
    # Setup mocks
    mock_file = MagicMock()
    mock_file.name = "temp.png"
    mock_temp.return_value = mock_file
    
    mock_img = MagicMock()
    mock_image_new.return_value = mock_img
    
    generator = SubtitleGenerator()
    path = generator._create_text_image("Test Text")
    
    assert path == "temp.png"
    mock_image_new.assert_called_once()
    mock_img.save.assert_called_with("temp.png", "PNG")
    assert "temp.png" in generator.temp_images

@patch('CreateShorts.Data_Gen.subtitle_generator.SubtitleGenerator._create_text_image')
@patch('CreateShorts.Data_Gen.subtitle_generator.ImageClip')
def test_create_subtitle_clips_v2(mock_image_clip_class, mock_create_image):
    # Setup mocks
    mock_create_image.return_value = "fake_path.png"
    
    mock_clip = MagicMock()
    # Chain methods: .set_position().set_start().set_duration()
    mock_image_clip_class.return_value.set_position.return_value.set_start.return_value.set_duration.return_value = mock_clip
    
    # Create ScriptDTO
    segments = [
        SegmentDTO(speaker="Nina", line="Hello", duration=2.0),
        SegmentDTO(speaker="Tina", line="World", duration=3.0)
    ]
    script = ScriptDTO(topic="Test", segments=segments)
    
    generator = SubtitleGenerator()
    clips = generator.create_subtitle_clips_v2(script)
    
    assert len(clips) == 2
    assert mock_create_image.call_count == 2
    assert mock_image_clip_class.call_count == 2

@patch('os.path.exists')
@patch('os.unlink')
def test_cleanup_temp_files(mock_unlink, mock_exists):
    mock_exists.return_value = True
    generator = SubtitleGenerator()
    generator.temp_images = ["file1.png", "file2.png"]
    
    generator.cleanup_temp_files()
    
    assert mock_unlink.call_count == 2
    assert len(generator.temp_images) == 0

@patch('CreateShorts.Data_Gen.subtitle_generator.ImageFont.truetype')
@patch('CreateShorts.Data_Gen.subtitle_generator.Image.new')
@patch('CreateShorts.Data_Gen.subtitle_generator.ImageDraw.Draw')
@patch('CreateShorts.Data_Gen.subtitle_generator.tempfile.NamedTemporaryFile')
@patch('os.path.exists')
def test_subtitle_readability_regression(mock_exists, mock_temp, mock_draw_class, mock_image_new, mock_truetype):
    """Ensure that the font size is not being divided and resulting in tiny text"""
    mock_exists.return_value = True
    mock_draw = mock_draw_class.return_value
    
    # Mock textbbox to return a height based on the font size used
    def side_effect_bbox(xy, text, font=None, **kwargs):
        # Simulate a font height of ~70% of fontsize
        fs = font.size if font else 40
        return (0, 0, fs * 5, fs * 0.7)
    
    mock_draw.textbbox.side_effect = side_effect_bbox
    
    generator = SubtitleGenerator()
    # We want to verify that ImageFont.truetype is called with the config fontsize
    # and NOT divided by 4.
    generator._create_text_image("Readable text")
    
    # Assert font was loaded with correct size
    args, _ = mock_truetype.call_args
    assert args[1] == generator.config.fontsize
    assert args[1] >= 150 # Should be at least our new default

