from typing import List
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from CreateShorts.Data_Gen.text_to_speach import AudioChunkInfo
from CreateShorts.Data_Gen.moviepy_config import *

@dataclass
class SubtitleConfig:
    """Configuración para el estilo de los subtítulos"""
    fontsize: int = 65  # Aumentado para mejor visibilidad
    font: str = 'Arial-Bold'
    color: str = 'white'
    stroke_color: str = 'black'
    stroke_width: int = 3  # Aumentado para mejor legibilidad
    size: tuple = (700, None)  # Reducido el ancho máximo para líneas más cortas
    method: str = 'caption'
    align: str = 'center'
    interline: int = -1

class SubtitleGenerator:
    def __init__(self, config: SubtitleConfig = None):
        self.config = config or SubtitleConfig()
    
    def create_subtitle_clips(self, audio_chunks: List[AudioChunkInfo]) -> List[TextClip]:
        """Crea y retorna los clips de subtítulos sin renderizar el video."""
        return self._create_subtitle_clips(audio_chunks)
    
    def _create_subtitle_clips(self, audio_chunks: List[AudioChunkInfo]) -> List[TextClip]:
        """Crea clips de subtítulos a partir de los chunks de audio."""
        subtitle_clips = []
        current_time = 0
        
        for chunk in audio_chunks:
            # Dividir el texto en frases más cortas si es necesario
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
                               interline=self.config.interline)
                       .set_position(('center', 0.80), relative=True)  # Ajustado para mejor posición
                       .set_start(current_time)
                       .set_duration(chunk.duration))
            
            subtitle_clips.append(txt_clip)
            current_time += chunk.duration
            
        return subtitle_clips

    def _optimize_text(self, text: str) -> str:
        """Optimiza el texto para mejor legibilidad."""
        # Eliminar espacios extras
        text = ' '.join(text.split())
        
        # Dividir en líneas más cortas si es necesario
        words = text.split()
        if len(words) > 6:  # Si hay más de 6 palabras
            mid = len(words) // 2
            return ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
        
        return text

    def add_subtitles(self, video_path: str, audio_chunks: List[AudioChunkInfo], 
                     output_path: str) -> None:
        """Agrega subtítulos al video basados en los chunks de audio."""
        try:
            print("-> Cargando video para agregar subtítulos...")
            video = VideoFileClip(video_path)
            
            print("-> Creando clips de subtítulos...")
            subtitle_clips = self._create_subtitle_clips(audio_chunks)
            
            print("-> Componiendo video final con subtítulos...")
            final_video = CompositeVideoClip([video] + subtitle_clips)
            
            print("-> Renderizando video con subtítulos...")
            final_video.write_videofile(
                output_path,
                fps=video.fps,
                codec='libx264',
                audio_codec='aac',
                threads=4
            )
            print(f"-> Video con subtítulos completado: {output_path}")
            
            # Cerrar los clips para liberar recursos
            video.close()
            final_video.close()
            for clip in subtitle_clips:
                clip.close()
            
        except Exception as e:
            print(f"Error al agregar subtítulos: {str(e)}")
            raise