import pytest
from unittest.mock import MagicMock, patch, call
from CreateShorts.Data_Gen.subtitle_generator import SubtitleGenerator, SubtitleConfig, CHUNK_SIZE, SUBTITLE_Y_RATIO
from CreateShorts.Models.script_models import ScriptDTO, SegmentDTO
from CreateShorts.config import VERTICAL_HEIGHT


def test_subtitle_config_defaults():
    config = SubtitleConfig()
    assert config.fontsize == 150
    assert config.color == 'white'


# --- _split_into_chunks ---

def test_split_into_chunks_short_text():
    gen = SubtitleGenerator()
    assert gen._split_into_chunks("Hello world") == ["Hello world"]


def test_split_into_chunks_exact_chunk_size():
    gen = SubtitleGenerator()
    text = "one two three four"
    assert gen._split_into_chunks(text) == ["one two three four"]


def test_split_into_chunks_long_text():
    gen = SubtitleGenerator()
    text = "one two three four five six seven eight"
    chunks = gen._split_into_chunks(text)
    assert len(chunks) == 2
    assert chunks[0] == "one two three four"
    assert chunks[1] == "five six seven eight"


def test_split_into_chunks_empty():
    gen = SubtitleGenerator()
    assert gen._split_into_chunks("") == []


def test_split_into_chunks_single_word():
    gen = SubtitleGenerator()
    assert gen._split_into_chunks("Hello") == ["Hello"]


# --- _create_text_image ---

@patch('CreateShorts.Data_Gen.subtitle_generator.ImageFont.truetype')
@patch('CreateShorts.Data_Gen.subtitle_generator.tempfile.NamedTemporaryFile')
@patch('CreateShorts.Data_Gen.subtitle_generator.Image.new')
def test_create_text_image_saves_and_tracks_file(mock_image_new, mock_temp, mock_truetype):
    mock_scratch = MagicMock()
    mock_scratch_draw = MagicMock()
    mock_scratch_draw.textbbox.return_value = (0, 0, 200, 50)
    mock_actual = MagicMock()

    mock_image_new.side_effect = [mock_scratch, mock_actual]

    with patch('CreateShorts.Data_Gen.subtitle_generator.ImageDraw.Draw',
               return_value=mock_scratch_draw):
        mock_file = MagicMock()
        mock_file.name = "temp.png"
        mock_temp.return_value = mock_file

        gen = SubtitleGenerator()
        path = gen._create_text_image("Test Text")

    assert path == "temp.png"
    assert "temp.png" in gen.temp_images
    mock_actual.save.assert_called_with("temp.png", "PNG")


@patch('CreateShorts.Data_Gen.subtitle_generator.ImageFont.truetype')
@patch('CreateShorts.Data_Gen.subtitle_generator.tempfile.NamedTemporaryFile')
@patch('CreateShorts.Data_Gen.subtitle_generator.Image.new')
@patch('os.path.exists')
def test_subtitle_readability_uses_configured_fontsize(mock_exists, mock_image_new, mock_temp, mock_truetype):
    """Font must be loaded with the configured fontsize — never divided or reduced."""
    mock_exists.return_value = True
    mock_scratch = MagicMock()
    mock_draw = MagicMock()
    mock_draw.textbbox.return_value = (0, 0, 300, 60)
    mock_actual = MagicMock()
    mock_image_new.side_effect = [mock_scratch, mock_actual]
    mock_temp.return_value = MagicMock(name="t.png")
    mock_temp.return_value.name = "t.png"

    with patch('CreateShorts.Data_Gen.subtitle_generator.ImageDraw.Draw', return_value=mock_draw):
        gen = SubtitleGenerator()
        gen._create_text_image("Readable text")

    args, _ = mock_truetype.call_args
    assert args[1] == gen.config.fontsize
    assert args[1] >= 150


# --- create_subtitle_clips_v2 ---

@patch('CreateShorts.Data_Gen.subtitle_generator.SubtitleGenerator._create_text_image')
@patch('CreateShorts.Data_Gen.subtitle_generator.ImageClip')
def test_single_word_segment_produces_one_clip(mock_image_clip_class, mock_create_image):
    mock_create_image.return_value = "fake.png"
    mock_clip = MagicMock()
    mock_image_clip_class.return_value.set_position.return_value.set_start.return_value.set_duration.return_value = mock_clip

    segments = [SegmentDTO(speaker="A", line="Hello", duration=2.0, start_time=0.0)]
    script = ScriptDTO(topic="T", segments=segments)

    gen = SubtitleGenerator()
    clips = gen.create_subtitle_clips_v2(script)

    assert len(clips) == 1


@patch('CreateShorts.Data_Gen.subtitle_generator.SubtitleGenerator._create_text_image')
@patch('CreateShorts.Data_Gen.subtitle_generator.ImageClip')
def test_long_segment_produces_multiple_chunks(mock_image_clip_class, mock_create_image):
    """8 words → 2 chunks of 4 → 2 clips."""
    mock_create_image.return_value = "fake.png"
    mock_clip = MagicMock()
    mock_image_clip_class.return_value.set_position.return_value.set_start.return_value.set_duration.return_value = mock_clip

    segments = [SegmentDTO(speaker="A", line="one two three four five six seven eight",
                           duration=4.0, start_time=0.0)]
    script = ScriptDTO(topic="T", segments=segments)

    gen = SubtitleGenerator()
    clips = gen.create_subtitle_clips_v2(script)

    assert len(clips) == 2
    assert mock_create_image.call_count == 2


@patch('CreateShorts.Data_Gen.subtitle_generator.SubtitleGenerator._create_text_image')
@patch('CreateShorts.Data_Gen.subtitle_generator.ImageClip')
def test_chunk_timing_uses_segment_start_time(mock_image_clip_class, mock_create_image):
    """Chunks must be timed from segment.start_time, not re-accumulated from scratch."""
    mock_create_image.return_value = "fake.png"
    chain = MagicMock()
    mock_image_clip_class.return_value.set_position.return_value = chain
    chain.set_start.return_value.set_duration.return_value = MagicMock()

    # Segment starts at 5.0s (simulating an SFX gap before it)
    segments = [SegmentDTO(speaker="A", line="one two three four five six seven eight",
                           duration=4.0, start_time=5.0)]
    script = ScriptDTO(topic="T", segments=segments)

    gen = SubtitleGenerator()
    gen.create_subtitle_clips_v2(script)

    start_calls = [c[0][0] for c in chain.set_start.call_args_list]
    # 2 chunks of 2s each: first at 5.0, second at 7.0
    assert abs(start_calls[0] - 5.0) < 0.01
    assert abs(start_calls[1] - 7.0) < 0.01


@patch('CreateShorts.Data_Gen.subtitle_generator.SubtitleGenerator._create_text_image')
@patch('CreateShorts.Data_Gen.subtitle_generator.ImageClip')
def test_subtitle_positioned_at_lower_third(mock_image_clip_class, mock_create_image):
    """Subtitles must be placed at ~80% of frame height, not center."""
    mock_create_image.return_value = "fake.png"
    mock_clip_chain = MagicMock()
    mock_image_clip_class.return_value.set_position.return_value = mock_clip_chain
    mock_clip_chain.set_start.return_value.set_duration.return_value = MagicMock()

    segments = [SegmentDTO(speaker="A", line="Hello", duration=2.0, start_time=0.0)]
    script = ScriptDTO(topic="T", segments=segments)

    gen = SubtitleGenerator()
    gen.create_subtitle_clips_v2(script)

    position_call = mock_image_clip_class.return_value.set_position.call_args[0][0]
    expected_y = int(VERTICAL_HEIGHT * SUBTITLE_Y_RATIO)
    assert position_call == ('center', expected_y)


# --- cleanup ---

@patch('os.path.exists')
@patch('os.unlink')
def test_cleanup_temp_files(mock_unlink, mock_exists):
    mock_exists.return_value = True
    gen = SubtitleGenerator()
    gen.temp_images = ["file1.png", "file2.png"]

    gen.cleanup_temp_files()

    assert mock_unlink.call_count == 2
    assert len(gen.temp_images) == 0
