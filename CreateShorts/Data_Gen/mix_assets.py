"""
Video Asset Mixer Module

This module handles the creation of vertical format videos (9:16) for social media platforms,
including audio mixing and video composition functionality.
"""

from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, ColorClip, CompositeVideoClip, TextClip
from PIL import Image
import os
from typing import Optional, List
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
        print(f"Error in create_looped_clip: {str(e)}")
        raise


def create_final_video(voice_path: str, music_path: str, video_background_path: str,
                       output_path: str, duration_sec: float,
                       subtitle_clips: List[TextClip] = None,
                       background_volume: float = 0.10) -> None:
    
    # Validación de entrada crítica
    if not voice_path or not os.path.exists(voice_path):
        raise ValueError(f"Voice file not found or invalid path: {voice_path}")
    
    if not video_background_path or not os.path.exists(video_background_path):
        raise ValueError(f"Background video file not found: {video_background_path}")
    
    # Crear directorio de salida si no existe
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 1. Get the REAL duration of the dialogue.
    try:
        voice_clip_temp = AudioFileClip(voice_path)
        dialogue_duration = voice_clip_temp.duration
        voice_clip_temp.close()  # Release the temporary clip.
    except Exception as e:
        raise ValueError(f"Failed to load voice file '{voice_path}': {str(e)}")

    # 2. CALCULATE FINAL DURATION: Dialogue + 0.5s Buffer.
    final_video_duration = dialogue_duration + AUDIO_BUFFER_SEC

    # 3. The cut and loop logic now uses the FINAL duration.
    try:
        background_clip = VideoFileClip(video_background_path)
    except Exception as e:
        raise ValueError(f"Failed to load background video '{video_background_path}': {str(e)}")

    if background_clip.duration < final_video_duration:
        video_clip_final = create_looped_clip(background_clip, final_video_duration)
        print(f"Alert: Background video looped to reach {final_video_duration:.2f}s")
    else:
        video_clip_final = background_clip.subclip(0, final_video_duration)

    try:
        # Create audio mix: WE PASS THE FINAL DURATION.
        master_audio = create_mixed_audio_clip(voice_path, music_path, final_video_duration, background_volume)

        # Load and format background video
        formatted_video = format_video_vertical(video_clip_final, final_video_duration)

        # Combine with subtitles if provided
        if subtitle_clips:
            formatted_video = CompositeVideoClip([formatted_video] + subtitle_clips)

        # Add audio
        final_clip = formatted_video.set_audio(master_audio)

        # Get dynamic render params based on hardware availability
        render_params = get_render_params()

        # Render final video
        print(f"-> Rendering final video with subtitles (9:16 Optimized) using {render_params['codec']}...")
        final_clip.write_videofile(
            output_path,
            fps=FPS,
            audio_codec=AUDIO_CODEC,
            logger=None,
            threads=4,
            **render_params
        )
        print(f"-> Video completed: {output_path}")

    except Exception as e:
        raise VideoMixingError(f"Failed to create final video: {str(e)}")
    finally:
        # Cleanup resources
        try:
            if 'background_clip' in locals():
                background_clip.close()
            if 'video_clip_final' in locals():
                video_clip_final.close()
            if 'formatted_video' in locals():
                formatted_video.close()
            if 'final_clip' in locals():
                final_clip.close()
            if 'master_audio' in locals():
                master_audio.close()
        except Exception as cleanup_error:
            print(f"⚠️ WARNING: Error during cleanup: {cleanup_error}")
