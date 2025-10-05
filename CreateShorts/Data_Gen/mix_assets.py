"""
Video Asset Mixer Module

This module handles the creation of vertical format videos (9:16) for social media platforms,
including audio mixing and video composition functionality.
"""

from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, ColorClip, CompositeVideoClip, TextClip
from PIL import Image
import os
from typing import Optional, List

# --- Video Format Constants ---
VERTICAL_WIDTH = 1080    # Width for vertical video format (9:16)
VERTICAL_HEIGHT = 1920   # Height for vertical video format (9:16)
BACKGROUND_VOLUME = 0.10 # Background music volume level (10% of original)
FPS = 30                 # Frames per second for output video
VIDEO_CODEC = 'libx264'  # Video codec for compatibility
AUDIO_CODEC = 'aac'      # Audio codec for compatibility

# Configuración para el redimensionamiento
Image.ANTIALIAS = Image.Resampling.LANCZOS

class VideoMixingError(Exception):
    """Custom exception for video mixing operations"""
    pass

def create_mixed_audio_clip(voice_path: str, music_path: str, duration_sec: float) -> CompositeAudioClip:
    """
    Creates a composite audio clip by mixing voice and background music.

    Args:
        voice_path (str): Path to the voice audio file
        music_path (str): Path to the background music file
        duration_sec (float): Desired duration in seconds

    Returns:
        CompositeAudioClip: Mixed audio clip with voice and background music

    Raises:
        VideoMixingError: If audio mixing fails
    """
    try:
        voice_clip = AudioFileClip(voice_path)
        music_clip = AudioFileClip(music_path)
        music_clip = music_clip.subclip(0, duration_sec)
        music_clip = music_clip.volumex(BACKGROUND_VOLUME)
        return CompositeAudioClip([voice_clip, music_clip]).set_duration(duration_sec)
    except Exception as e:
        raise VideoMixingError(f"Failed to create mixed audio: {str(e)}")

def format_video_vertical(video_clip: VideoFileClip, duration_sec: float) -> CompositeVideoClip:
    """
    Formats a video clip to vertical 9:16 format with centered content.

    Args:
        video_clip (VideoFileClip): Input video clip to format
        duration_sec (float): Desired duration in seconds

    Returns:
        CompositeVideoClip: Formatted vertical video clip
    """
    # Cut to desired duration
    video_cut = video_clip.subclip(0, duration_sec)
    
    # Scale to cover full width
    video_resized = video_cut.resize(width=VERTICAL_WIDTH)
    
    # Create black vertical canvas
    canvas = ColorClip(
        size=(VERTICAL_WIDTH, VERTICAL_HEIGHT),
        color=(0, 0, 0),
        duration=duration_sec
    )
    
    # Compose video on canvas
    return CompositeVideoClip([
        canvas,
        video_resized.set_pos("center")
    ])

def create_final_video(voice_path: str, music_path: str, video_background_path: str, 
                      output_path: str, duration_sec: float, 
                      subtitle_clips: List[TextClip] = None) -> None:
    """
    Creates a final vertical format video with mixed audio and subtitles.
    
    Args:
        voice_path: Path to voice audio file
        music_path: Path to background music file
        video_background_path: Path to background video file
        output_path: Path for output video file
        duration_sec: Desired video duration in seconds
        subtitle_clips: Optional list of subtitle clips to add
    """
    try:
        # Create audio mix
        master_audio = create_mixed_audio_clip(voice_path, music_path, duration_sec)
        
        # Load and format background video
        background_clip = VideoFileClip(video_background_path)
        formatted_video = format_video_vertical(background_clip, duration_sec)
        
        # Combine with subtitles if provided
        if subtitle_clips:
            formatted_video = CompositeVideoClip([formatted_video] + subtitle_clips)
        
        # Add audio
        final_clip = formatted_video.set_audio(master_audio)

        # Render final video
        print("-> Rendering final video with subtitles (9:16 Optimized)...")
        final_clip.write_videofile(
            output_path,
            fps=FPS,
            codec=VIDEO_CODEC,
            audio_codec=AUDIO_CODEC,
            logger=None,
            threads=4
        )
        print(f"-> Video completed: {output_path}")

    except Exception as e:
        raise VideoMixingError(f"Failed to create final video: {str(e)}")