"""
Video Asset Mixer Module

This module handles the creation of vertical format videos (9:16) for social media platforms,
including audio mixing and video composition functionality.
"""

import logging
import os
from typing import Optional, List
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, TextClip
from PIL import Image

logger = logging.getLogger(__name__)
from moviepy.editor import concatenate_videoclips, concatenate_audioclips
from CreateShorts.Data_Gen.moviepy_config import get_render_params

# --- Video Format Constants ---
VERTICAL_WIDTH = 1080    # Width for vertical video format (9:16).
VERTICAL_HEIGHT = 1920   # Height for vertical video format (9:16)
BACKGROUND_VOLUME = 0.10 # Background music volume level (10% of original)
FPS = 30                 # Frames per second for output video
VIDEO_CODEC = 'libx264'  # Video codec for compatibility
AUDIO_CODEC = 'aac'      # Audio codec for compatibility
AUDIO_BUFFER_SEC = 0.5

Image.ANTIALIAS = Image.Resampling.LANCZOS


class VideoMixingError(Exception):
    """Custom exception for video mixing operations"""
    pass


def create_mixed_audio_clip(voice_path: str, music_path: str, duration_sec: float,
                            background_volume: float = 0.10) -> CompositeAudioClip:
    try:
        # Validar archivos de entrada
        if not voice_path or not os.path.exists(voice_path):
            raise ValueError(f"Voice file not found: {voice_path}")
        if not music_path or not os.path.exists(music_path):
            raise ValueError(f"Music file not found: {music_path}")
            
        voice_clip = AudioFileClip(voice_path)
        music_clip = AudioFileClip(music_path)

        # If the music is shorter, we create loops manually.
        if music_clip.duration < duration_sec:
            num_loops = int(duration_sec / music_clip.duration) + 1
            music_clips = [music_clip] * num_loops
            music_clip = concatenate_audioclips(music_clips)

        # The music is cut to duration_sec (dialogue + buffer).
        music_clip = music_clip.subclip(0, duration_sec)
        
        # We adjust the music volume.
        music_clip = music_clip.volumex(background_volume)

        return CompositeAudioClip([voice_clip, music_clip]).set_duration(duration_sec)

    except Exception as e:
        raise VideoMixingError(f"Failed to create mixed audio: {str(e)}")

def format_video_vertical(video_clip: VideoFileClip, duration_sec: float) -> VideoFileClip:
    """
    Formats a video clip to vertical 9:16 format using crop-to-fill.
    Scales the input uniformly so it covers the full 1080x1920 canvas,
    then center-crops to exact dimensions. No black bars regardless of input aspect ratio.

    Args:
        video_clip (VideoFileClip): Input video clip to format
        duration_sec (float): Desired duration in seconds

    Returns:
        VideoFileClip: Cropped vertical video clip (1080x1920)
    """
    video_cut = video_clip.subclip(0, duration_sec)

    src_w, src_h = video_cut.size
    scale = max(VERTICAL_WIDTH / src_w, VERTICAL_HEIGHT / src_h)
    video_scaled = video_cut.resize(scale)

    return video_scaled.crop(
        x_center=video_scaled.w / 2,
        y_center=video_scaled.h / 2,
        width=VERTICAL_WIDTH,
        height=VERTICAL_HEIGHT
    )

def create_looped_clip(clip: VideoFileClip, target_duration: float) -> VideoFileClip:
    """
    Creates a looped video clip from the given clip to ensure it reaches
    or exceeds the target duration. The resulting video clip is truncated
    to exactly match the target duration.

    :param clip: The source video clip to be looped.
    :type clip: VideoFileClip
    :param target_duration: The desired duration of the final video, in seconds.
    :type target_duration: float
    :return: A new video clip object with a looped and truncated version of the source clip.
    :rtype: VideoFileClip
    :raises Exception: If an error occurs during the looping or concatenation process.
    """
    try:
        num_repeats = int(target_duration / clip.duration) + 1
        clips = [clip.copy() for _ in range(num_repeats)]
        concatenated = concatenate_videoclips(clips)
        result = concatenated.subclip(0, target_duration)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in create_looped_clip: {str(e)}")
        raise


def _get_dialogue_duration(voice_path: str) -> float:
    """Returns the real duration of the dialogue audio file in seconds."""
    try:
        clip = AudioFileClip(voice_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        raise ValueError(f"Failed to load voice file '{voice_path}': {str(e)}")


def _prepare_background_clip(video_path: str, target_duration: float) -> VideoFileClip:
    """Loads and loops/trims the background video to match target_duration."""
    try:
        clip = VideoFileClip(video_path)
    except Exception as e:
        raise ValueError(f"Failed to load background video '{video_path}': {str(e)}")

    if clip.duration < target_duration:
        looped = create_looped_clip(clip, target_duration)
        logger.info(f"Background video looped to reach {target_duration:.2f}s")
        return looped
    return clip.subclip(0, target_duration)


def _render_video(formatted_video, master_audio, subtitle_clips, output_path: str):
    """Composites subtitles, attaches audio, and writes the final video file."""
    if subtitle_clips:
        formatted_video = CompositeVideoClip([formatted_video] + subtitle_clips)

    final_clip = formatted_video.set_audio(master_audio)
    render_params = get_render_params()

    logger.info(f"Rendering final video (9:16) using codec: {render_params['codec']}")
    final_clip.write_videofile(
        output_path,
        fps=FPS,
        audio_codec=AUDIO_CODEC,
        logger=None,
        threads=4,
        **render_params
    )
    logger.info(f"Video completed: {output_path}")
    return final_clip


def create_final_video(voice_path: str, music_path: str, video_background_path: str,
                       output_path: str, duration_sec: float,
                       subtitle_clips: List[TextClip] = None,
                       background_volume: float = 0.10) -> None:

    if not voice_path or not os.path.exists(voice_path):
        raise ValueError(f"Voice file not found or invalid path: {voice_path}")
    if not video_background_path or not os.path.exists(video_background_path):
        raise ValueError(f"Background video file not found: {video_background_path}")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    final_duration = _get_dialogue_duration(voice_path) + AUDIO_BUFFER_SEC

    background_clip = None
    master_audio = None
    formatted_video = None
    final_clip = None

    try:
        background_clip = _prepare_background_clip(video_background_path, final_duration)
        master_audio = create_mixed_audio_clip(voice_path, music_path, final_duration, background_volume)
        formatted_video = format_video_vertical(background_clip, final_duration)
        final_clip = _render_video(formatted_video, master_audio, subtitle_clips, output_path)

    except Exception as e:
        raise VideoMixingError(f"Failed to create final video: {str(e)}")
    finally:
        for clip in [background_clip, master_audio, formatted_video, final_clip]:
            if clip is not None:
                try:
                    clip.close()
                except Exception as cleanup_error:
                    logger.warning(f"Error during cleanup: {cleanup_error}")
