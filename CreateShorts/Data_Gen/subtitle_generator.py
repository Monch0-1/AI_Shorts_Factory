from typing import List
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os

from CreateShorts.Models.script_models import ScriptDTO

@dataclass
class SubtitleConfig:
    """Configuration for the subtitle style"""
    fontsize: int = 170  # Increased for better visibility
    font: str = 'Arial-Bold'
    color: str = 'white'
    stroke_color: str = 'black'
    stroke_width: int = 4  # Increased for better readability
    size: tuple = (700, None)  # Reduced max width for shorter lines
    method: str = 'caption'
    align: str = 'center'
    interline: int = -1

class SubtitleGenerator:
    def __init__(self, config: SubtitleConfig = None):
        self.config = config or SubtitleConfig()
        self.temp_images = []  # Para limpiar archivos temporales

    def _create_text_image(self, text: str) -> str:
        """Creates a text image using PIL and returns the temporary file path"""
        try:
            # Configuración de imagen
            img_width = 1080
            img_height = 200
            
            # Crear imagen transparente
            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Intentar cargar fuente, con fallback
            try:
                # Buscar fuente del sistema
                if os.name == 'nt':  # Windows
                    font_path = "C:/Windows/Fonts/arialbd.ttf"  # Arial Bold
                    if not os.path.exists(font_path):
                        font_path = "C:/Windows/Fonts/arial.ttf"  # Arial regular
                else:  # Linux/Mac
                    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, self.config.fontsize // 4)  # Ajustar tamaño
                else:
                    font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            
            # Calcular posición del texto (centrado)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (img_width - text_width) // 2
            y = (img_height - text_height) // 2
            
            # Dibujar contorno (stroke)
            if self.config.stroke_width > 0:
                for adj_x in range(-self.config.stroke_width, self.config.stroke_width + 1):
                    for adj_y in range(-self.config.stroke_width, self.config.stroke_width + 1):
                        if adj_x != 0 or adj_y != 0:
                            draw.text((x + adj_x, y + adj_y), text, font=font, fill=self.config.stroke_color)
            
            # Dibujar texto principal
            draw.text((x, y), text, font=font, fill=self.config.color)
            
            # Guardar imagen temporal
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            img.save(temp_path, 'PNG')
            self.temp_images.append(temp_path)  # Para limpieza posterior
            
            return temp_path
            
        except Exception as e:
            print(f"❌ Error creating text image: {e}")
            # Crear imagen simple como fallback
            img = Image.new('RGBA', (800, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((50, 25), text[:50], fill='white')  # Texto simple
            
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            img.save(temp_path, 'PNG')
            self.temp_images.append(temp_path)
            
            return temp_path

    def create_subtitle_clips_v2(self, script_dto: ScriptDTO) -> List[ImageClip]:
        subtitle_clips = []
        current_time = 0.0

        print("-> Creating subtitle clips from DTO using PIL...")

        for segment in script_dto.segments:
            # Optimizar el texto
            text = self._optimize_text(segment.line)

            try:
                # Crear imagen de texto
                image_path = self._create_text_image(text)
                
                # Crear clip de imagen
                img_clip = (ImageClip(image_path)
                          .set_position(('center', 'center'))
                          .set_start(current_time)
                          .set_duration(segment.duration))

                subtitle_clips.append(img_clip)
                
            except Exception as e:
                print(f"❌ Error creating subtitle clip: {e}")
                continue

            current_time += segment.duration

        return subtitle_clips

    def _optimize_text(self, text: str) -> str:
        text = ' '.join(text.split())
        words = text.split()
        if len(words) > 6:
            mid = len(words) // 2
            return ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
        return text

    def cleanup_temp_files(self):
        """Limpia archivos temporales creados"""
        for temp_path in self.temp_images:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                print(f"⚠️ Warning: Could not delete temp file {temp_path}: {e}")
        self.temp_images.clear()

    def add_subtitles_v2(self, video_path: str, script_dto: ScriptDTO, output_path: str) -> None:
        global video, final_video, subtitle_clips
        try:
            print("-> Loading video to add subtitles...")
            video = VideoFileClip(video_path)

            print("-> Creating subtitle clips from DTO...")
            subtitle_clips = self.create_subtitle_clips_v2(script_dto)

            print("-> Composing final video with subtitles...")
            final_video = CompositeVideoClip([video] + subtitle_clips)

            print("-> Rendering video with subtitles...")
            final_video.write_videofile(
                output_path,
                fps=video.fps,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                logger=None
            )
            print(f"-> Video with subtitles completed: {output_path}")

        except Exception as e:
            print(f"❌ Error adding subtitles: {str(e)}")
            raise
        finally:
            if 'video' in locals(): video.close()
            if 'final_video' in locals(): final_video.close()
            if 'subtitle_clips' in locals():
                for clip in subtitle_clips:
                    clip.close()
            # Limpiar archivos temporales
            self.cleanup_temp_files()