import pytest
from unittest.mock import MagicMock, patch
from CreateShorts.Data_Gen.mix_assets import create_mixed_audio_clip, format_video_vertical, create_looped_clip, VideoMixingError

@patch('CreateShorts.Data_Gen.mix_assets.AudioFileClip')
@patch('os.path.exists')
def test_create_mixed_audio_clip_success(mock_exists, mock_audio_clip_class):
    mock_exists.return_value = True
    
    mock_voice = MagicMock()
    mock_voice.duration = 10.0
    
    mock_music = MagicMock()
    mock_music.duration = 60.0
    
    # Side effect to return voice then music clip
    mock_audio_clip_class.side_effect = [mock_voice, mock_music]
    
    with patch('CreateShorts.Data_Gen.mix_assets.CompositeAudioClip') as mock_composite:
        mock_composite.return_value.set_duration.return_value = MagicMock()
        
        result = create_mixed_audio_clip("voice.mp3", "music.mp3", 15.0)
        
        assert result is not None
        mock_audio_clip_class.assert_any_call("voice.mp3")
        mock_audio_clip_class.assert_any_call("music.mp3")
        mock_music.subclip.assert_called_with(0, 15.0)
        mock_music.subclip.return_value.volumex.assert_called_with(0.10)

@patch('CreateShorts.Data_Gen.mix_assets.AudioFileClip')
@patch('CreateShorts.Data_Gen.mix_assets.concatenate_audioclips')
@patch('os.path.exists')
def test_create_mixed_audio_clip_looping(mock_exists, mock_concat, mock_audio_clip_class):
    mock_exists.return_value = True
    
    mock_voice = MagicMock()
    mock_voice.duration = 10.0
    
    mock_music = MagicMock()
    mock_music.duration = 5.0 # Shorter than 15.0
    
    mock_audio_clip_class.side_effect = [mock_voice, mock_music]
    
    with patch('CreateShorts.Data_Gen.mix_assets.CompositeAudioClip') as mock_composite:
        mock_composite.return_value.set_duration.return_value = MagicMock()
        
        create_mixed_audio_clip("voice.mp3", "music.mp3", 15.0)
        
        # Should loop music approx 4 times (15/5 + 1)
        assert mock_concat.called
        args, _ = mock_concat.call_args
        assert len(args[0]) == 4

def test_format_video_vertical_16_9_crops_to_fill():
    """16:9 input (1920x1080) must scale to cover 1080x1920 and center-crop — no black bars."""
    mock_cut = MagicMock()
    mock_cut.size = (1920, 1080)

    # scale = max(1080/1920, 1920/1080) = max(0.5625, 1.778) = 1.778
    mock_scaled = MagicMock()
    mock_scaled.w = round(1920 * (1920 / 1080))  # 3413
    mock_scaled.h = 1920
    mock_cut.resize.return_value = mock_scaled

    mock_cropped = MagicMock()
    mock_scaled.crop.return_value = mock_cropped

    mock_video = MagicMock()
    mock_video.subclip.return_value = mock_cut

    result = format_video_vertical(mock_video, 10.0)

    mock_video.subclip.assert_called_with(0, 10.0)
    scale_used = mock_cut.resize.call_args[0][0]
    assert abs(scale_used - (1920 / 1080)) < 0.01  # ~1.778
    mock_scaled.crop.assert_called_once_with(
        x_center=mock_scaled.w / 2,
        y_center=mock_scaled.h / 2,
        width=1080,
        height=1920
    )
    assert result is mock_cropped


def test_format_video_vertical_9_16_no_upscale_needed():
    """Native 9:16 input (1080x1920) — scale factor is 1.0, crop is a no-op passthrough."""
    mock_cut = MagicMock()
    mock_cut.size = (1080, 1920)

    mock_scaled = MagicMock()
    mock_scaled.w = 1080
    mock_scaled.h = 1920
    mock_cut.resize.return_value = mock_scaled

    mock_video = MagicMock()
    mock_video.subclip.return_value = mock_cut

    format_video_vertical(mock_video, 10.0)

    scale_used = mock_cut.resize.call_args[0][0]
    assert abs(scale_used - 1.0) < 0.01

@patch('CreateShorts.Data_Gen.mix_assets.concatenate_videoclips')
def test_create_looped_clip(mock_concat):
    mock_clip = MagicMock()
    mock_clip.duration = 5.0
    mock_clip.copy.return_value = mock_clip
    
    target_duration = 12.0
    create_looped_clip(mock_clip, target_duration)
    
    # 12 / 5 + 1 = 3
    assert mock_clip.copy.call_count == 3
    mock_concat.assert_called_once()
    mock_concat.return_value.subclip.assert_called_with(0, 12.0)

def test_create_mixed_audio_clip_file_not_found():
    with patch('os.path.exists', return_value=False):
        with pytest.raises(VideoMixingError) as excinfo:
            create_mixed_audio_clip("none.mp3", "music.mp3", 10.0)
        assert "Voice file not found" in str(excinfo.value)
