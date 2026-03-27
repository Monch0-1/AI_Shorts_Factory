from typing import List
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os

from CreateShorts.Models.script_models import ScriptDTO
from CreateShorts.Data_Gen.moviepy_config import get_render_params
from CreateShorts.config import VERTICAL_HEIGHT

CHUNK_SIZE = 4              # Max words per subtitle chunk
SUBTITLE_Y_RATIO = 0.80     # Vertical position as fraction of frame height (lower-third)
PILL_PAD_X = 24             # Horizontal padding inside pill background
PILL_PAD_Y = 10             # Vertical padding inside pill background
PILL_RADIUS = 14            # Corner radius of pill background
PILL_FILL = (0, 0, 0, 160)  # Semi-transparent black


@dataclass
class SubtitleConfig:
    """Configuration for the subtitle style"""
    fontsize: int = 150
    font: str = 'Impact'
    color: str = 'white'
    stroke_color: str = 'black'
    stroke_width: int = 6
    size: tuple = (800, None)
    method: str = 'caption'
    align: str = 'center'
    interline: int = -1


class SubtitleGenerator:
    def __init__(self, config: SubtitleConfig = None):
        self.config = config or SubtitleConfig()
        self.temp_images = []

    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Loads the configured font with fallback to system default."""
        try:
            if os.name == 'nt':
                font_path = "C:/Windows/Fonts/impact.ttf"
                if not os.path.exists(font_path):
                    font_path = "C:/Windows/Fonts/arialbd.ttf"
            else:
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, self.config.fontsize)
        except Exception:
            pass
        return ImageFont.load_default()

    def _split_into_chunks(self, text: str) -> List[str]:
        """Splits text into chunks of up to CHUNK_SIZE words for word-paced display."""
        words = ' '.join(text.split()).split()
        if not words:
            return [text] if text.strip() else []
        return [' '.join(words[i:i + CHUNK_SIZE]) for i in range(0, len(words), CHUNK_SIZE)]

    def _create_text_image(self, text: str) -> str:
        """
        Creates a centered text image with a semi-transparent pill background.
        Text is always horizontally centered regardless of length.
        """
        img_width = 1080
        font = self._load_font()

        try:
            # Measure text on a minimal scratch surface
            scratch = Image.new('RGBA', (1, 1))
            draw = ImageDraw.Draw(scratch)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            img_height = text_h + PILL_PAD_Y * 2 + 10

            img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Pill: centered horizontally around the text
            pill_x1 = (img_width - text_w) // 2 - PILL_PAD_X
            pill_y1 = 5
            pill_x2 = (img_width + text_w) // 2 + PILL_PAD_X
            pill_y2 = img_height - 5

            try:
                draw.rounded_rectangle([pill_x1, pill_y1, pill_x2, pill_y2],
                                       radius=PILL_RADIUS, fill=PILL_FILL)
            except AttributeError:
                # Pillow < 8.2 fallback
                draw.rectangle([pill_x1, pill_y1, pill_x2, pill_y2], fill=PILL_FILL)

            # Text centered horizontally
            text_x = (img_width - text_w) // 2
            text_y = PILL_PAD_Y + 5

            # Stroke
            if self.config.stroke_width > 0:
                for dx in range(-self.config.stroke_width, self.config.stroke_width + 1):
                    for dy in range(-self.config.stroke_width, self.config.stroke_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((text_x + dx, text_y + dy), text,
                                      font=font, fill=self.config.stroke_color)

            # Main text
            draw.text((text_x, text_y), text, font=font, fill=self.config.color)

        except Exception as e:
            print(f"❌ Error creating text image: {e}")
            img = Image.new('RGBA', (img_width, 80), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((20, 20), text[:50], fill='white')

        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        img.save(temp_path, 'PNG')
        self.temp_images.append(temp_path)
        return temp_path

    def create_subtitle_clips_v2(self, script_dto: ScriptDTO) -> List[ImageClip]:
        subtitle_clips = []
        y_pos = int(VERTICAL_HEIGHT * SUBTITLE_Y_RATIO)

        print("-> Creating subtitle clips from DTO using PIL...")

        for segment in script_dto.segments:
            chunks = self._split_into_chunks(segment.line)
            if not chunks:
                continue

            chunk_duration = segment.duration / len(chunks)

            for i, chunk in enumerate(chunks):
                chunk_start = segment.start_time + i * chunk_duration
                try:
                    image_path = self._create_text_image(chunk)
                    img_clip = (ImageClip(image_path)
                                .set_position(('center', y_pos))
                                .set_start(chunk_start)
                                .set_duration(chunk_duration))
                    subtitle_clips.append(img_clip)
                except Exception as e:
                    print(f"❌ Error creating subtitle clip: {e}")
                    continue

        return subtitle_clips

    def cleanup_temp_files(self):
        """Cleans up temporary image files created during subtitle generation."""
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

            render_params = get_render_params()

            print(f"-> Rendering video with subtitles using {render_params['codec']}...")
            final_video.write_videofile(
                output_path,
                fps=video.fps,
                audio_codec='aac',
                threads=4,
                logger=None,
                **render_params
            )
            print(f"-> Video with subtitles completed: {output_path}")

        except Exception as e:
            print(f"❌ Error adding subtitles: {str(e)}")
            raise
        finally:
            if 'video' in locals():
                video.close()
            if 'final_video' in locals():
                final_video.close()
            if 'subtitle_clips' in locals():
                for clip in subtitle_clips:
                    clip.close()
            self.cleanup_temp_files()
