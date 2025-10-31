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

# --- Video Format Constants ---
VERTICAL_WIDTH = 1080    # Width for vertical video format (9:16)
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
        voice_clip = AudioFileClip(voice_path)
        music_clip = AudioFileClip(music_path)

        # Si la música es más corta, creamos loops manualmente
        if music_clip.duration < duration_sec:
            num_loops = int(duration_sec / music_clip.duration) + 1
            music_clips = [music_clip] * num_loops
            music_clip = concatenate_audioclips(music_clips)

        # La música se corta a la duración_sec (diálogo + buffer)
        music_clip = music_clip.subclip(0, duration_sec)
        
        # Ajustamos el volumen de la música
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
        print(f"Error en create_looped_clip: {str(e)}")
        raise


def create_final_video(voice_path: str, music_path: str, video_background_path: str,
                       output_path: str, duration_sec: float,
                       subtitle_clips: List[TextClip] = None,
                       background_volume: float = 0.10) -> None:
    # 1. Obtener la duración REAL del diálogo
    voice_clip_temp = AudioFileClip(voice_path)
    dialogue_duration = voice_clip_temp.duration
    voice_clip_temp.close()  # Liberar el clip temporal

    # 2. CALCULAR LA DURACIÓN FINAL: Diálogo + Buffer de 0.5s
    final_video_duration = dialogue_duration + AUDIO_BUFFER_SEC

    # 3. La lógica de corte y loop ahora usa la duración FINAL
    background_clip = VideoFileClip(video_background_path)

    if background_clip.duration < final_video_duration:
        video_clip_final = create_looped_clip(background_clip, final_video_duration)
        print(f"Alerta: Video de fondo loopeado para alcanzar {final_video_duration:.2f}s")
    else:
        video_clip_final = background_clip.subclip(0, final_video_duration)

    try:
        # Create audio mix: PASAMOS LA DURACIÓN FINAL
        master_audio = create_mixed_audio_clip(voice_path, music_path, final_video_duration, background_volume)

        # Load and format background video
        # CORRECCIÓN: Usar el clip ajustado (video_clip_final) para el formateo vertical
        formatted_video = format_video_vertical(video_clip_final, final_video_duration)

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