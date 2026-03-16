import shutil
from pathlib import Path
from CreateShorts.Interfaces.interfaces import IAudioService, IScriptService
from CreateShorts.Models.script_models import ScriptDTO
from CreateShorts.utils import sanitize_filename
from CreateShorts.theme_config import ThemeConfig
import os
from typing import List
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip

# Configurar FFmpeg explícitamente al importar el módulo
try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe
    print(f"🔧 [CONFIG] FFmpeg configured at: {ffmpeg_exe}")
except ImportError:
    print("⚠️ [WARNING] imageio-ffmpeg not found, FFmpeg auto-detection may fail")
except Exception as e:
    print(f"⚠️ [WARNING] FFmpeg configuration failed: {e}")

# Obtener la ruta del directorio del proyecto de forma más robusta
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Ir 3 niveles arriba desde service_mock.py
TEMP_DIR = PROJECT_ROOT / "MockAudioFiles" / "CreateShorts" / "resources" / "audio" / "temp_audio"
MOCK_DIR = PROJECT_ROOT / "resources" / "audio" / "mocks"


class MockAudioService(IAudioService):
    def synthesize(self, script: ScriptDTO, theme: ThemeConfig) -> ScriptDTO:
        print("🛡️ [MOCK MODE] Simulating Audio using local resources...")
        print(f"🛡️ [DEBUG] MOCK_DIR path: {MOCK_DIR}")
        print(f"🛡️ [DEBUG] MOCK_DIR exists: {MOCK_DIR.exists()}")
        
        # Crear directorios si no existen
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        MOCK_DIR.mkdir(parents=True, exist_ok=True)

        for i, segment in enumerate(script.segments):
            # Buscamos un audio que se llame igual que el speaker (Nina.mp3, Tina.mp3)
            mock_source = MOCK_DIR / f"{segment.speaker}.mp3"

            # Si no existe, usamos un "fallback.mp3" que tengas ahí
            if not mock_source.exists():
                mock_source = MOCK_DIR / "fallback.mp3"
                print(f"🛡️ [DEBUG] Using fallback: {mock_source}")
                print(f"🛡️ [DEBUG] Fallback exists: {mock_source.exists()}")

            file_name = f"mock_seg_{i}_{segment.speaker}.mp3"
            chunk_path = TEMP_DIR / file_name

            # Verificar que el archivo fuente existe antes de copiarlo
            if not mock_source.exists():
                print(f"❌ [ERROR] Mock source file not found: {mock_source}")
                print(f"💡 [INFO] Available files in MOCK_DIR:")
                if MOCK_DIR.exists():
                    for file in MOCK_DIR.iterdir():
                        print(f"   - {file.name}")
                else:
                    print("   - Directory does not exist!")
                continue

            try:
                # En lugar de API, copiamos el archivo local
                shutil.copy(str(mock_source), str(chunk_path))

                # Configurar FFmpeg antes de usar AudioFileClip
                try:
                    # Obtenemos la duración real del archivo copiado
                    with AudioFileClip(str(chunk_path)) as audio_clip:
                        segment.duration = audio_clip.duration
                except Exception as ffmpeg_error:
                    print(f"⚠️ [WARNING] MoviePy error (using fallback duration): {ffmpeg_error}")
                    # Usar duración estimada basada en tamaño del archivo como fallback
                    file_size_mb = chunk_path.stat().st_size / (1024 * 1024)
                    # Estimación aproximada: ~1MB por minuto de audio MP3 a 128kbps
                    segment.duration = max(1.0, file_size_mb * 60)

                segment.audio_path = str(chunk_path)
                print(f"   [MOCK OK] {segment.duration:.2f}s | Path: {file_name}")
                
            except Exception as e:
                print(f"❌ [ERROR] Failed to process {segment.speaker}: {e}")

        return script


class MockScriptService(IScriptService):
    def generate(self, topic: str, time_limit: int, theme_config: ThemeConfig,
                 context: str = None, use_template: bool = False, is_monologue: bool = False,
                 enable_refiner: bool = False) -> str:
        # Usar rutas absolutas también aquí
        debug_scripts_dir = PROJECT_ROOT / "MockScriptFiles"
        
        # Intentamos buscar un archivo que coincida con el tópico
        sanitized_topic = sanitize_filename(topic)
        mock_path = debug_scripts_dir / f"{sanitized_topic}.json"

        # Fallback si no existe el archivo específico
        if not mock_path.exists():
            fallback_path = debug_scripts_dir / "5_Everyday_Myths_You_Still_Believe_But_Arent_True.json"
            if fallback_path.exists():
                mock_path = fallback_path
            else:
                print(f"❌ [ERROR] No mock scripts found in: {debug_scripts_dir}")
                return '[]'  # Retornar script vacío como fallback

        print(f"🛡️ [MOCK MODE] Reading local script: {mock_path}")
        try:
            with open(mock_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"❌ [ERROR] Failed to read script: {e}")
            return '[]'
# Configurar FFmpeg al inicio del módulo
try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe
    print(f"🔧 [CONFIG] FFmpeg configured at: {ffmpeg_exe}")
except ImportError:
    print("⚠️ [WARNING] imageio-ffmpeg not found, installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"])
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe
    print(f"🔧 [CONFIG] FFmpeg configured at: {ffmpeg_exe}")
except Exception as e:
    print(f"⚠️ [WARNING] FFmpeg configuration failed: {e}")

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
        # CORRECTION: Use the adjusted clip (video_clip_final) for vertical formatting.
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