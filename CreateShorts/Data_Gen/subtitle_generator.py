from typing import List
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from CreateShorts.Data_Gen.text_to_speach import AudioChunkInfo
from CreateShorts.Data_Gen.moviepy_config import *

@dataclass
class SubtitleConfig:
    """Configuration for the subtitle style"""
    fontsize: int = 65  # Increased for better visibility
    font: str = 'Arial-Bold'
    color: str = 'white'
    stroke_color: str = 'black'
    stroke_width: int = 3  # Increased for better readability
    size: tuple = (700, None)  # Reduced max width for shorter lines
    method: str = 'caption'
    align: str = 'center'
    interline: int = -1

class SubtitleGenerator:
    def __init__(self, config: SubtitleConfig = None):
        self.config = config or SubtitleConfig()
    
    def create_subtitle_clips(self, audio_chunks: List[AudioChunkInfo]) -> List[TextClip]:
        """Creates and returns subtitle clips without rendering the video."""
        return self._create_subtitle_clips(audio_chunks)
    
    def _create_subtitle_clips(self, audio_chunks: List[AudioChunkInfo]) -> List[TextClip]:
        """Creates subtitle clips from audio chunks."""
        subtitle_clips = []
        current_time = 0
        
        for chunk in audio_chunks:
            # Split text into shorter phrases if necessary
            text = self._optimize_text(chunk.text)
            
            txt_clip = (TextClip(text,
                               fontsize=self.config.fontsize,
                               font=self.config.font,
                               color=self.config.color,
                               stroke_color=self.config.stroke_color,
                               stroke_width=self.config.stroke_width,
                               method=self.config.method,
                               size=self.config.size,
                               align=self.config.align,
                               interline=self.config.interline) # Adjusted for better position
                       .set_position(('center', 0.80), relative=True)
                       .set_start(current_time)
                       .set_duration(chunk.duration))
            
            subtitle_clips.append(txt_clip)
            current_time += chunk.duration
            
        return subtitle_clips

    def _optimize_text(self, text: str) -> str:
        """Optimizes text for better readability."""
        # Remove extra spaces
        text = ' '.join(text.split())
        
        # Split into shorter lines if necessary
        words = text.split()
        if len(words) > 6:  # If there are more than 6 words
            mid = len(words) // 2
            return ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
        
        return text

    def add_subtitles(self, video_path: str, audio_chunks: List[AudioChunkInfo], 
                     output_path: str) -> None:
        """Adds subtitles to the video based on audio chunks."""
        try:
            print("-> Loading video to add subtitles...")
            video = VideoFileClip(video_path)
            
            print("-> Creating subtitle clips...")
            subtitle_clips = self._create_subtitle_clips(audio_chunks)
            
            print("-> Composing final video with subtitles...")
            final_video = CompositeVideoClip([video] + subtitle_clips)
            
            print("-> Rendering video with subtitles...")
            final_video.write_videofile(
                output_path,
                fps=video.fps,
                codec='libx264',
                audio_codec='aac',
                threads=4
            )
            print(f"-> Video with subtitles completed: {output_path}")
            
            # Close clips to free up resources
            video.close()
            final_video.close()
            for clip in subtitle_clips:
                clip.close()
            
        except Exception as e:
            print(f"Error adding subtitles: {str(e)}")
            raise