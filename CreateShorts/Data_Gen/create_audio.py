import os
import random
from moviepy.editor import AudioFileClip, CompositeAudioClip
from CreateShorts.Models.script_models import ScriptDTO
from CreateShorts.theme_config import ThemeConfig

# Configurar FFmpeg al inicio del módulo
try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe
    print(f"🔧 [CONFIG] FFmpeg configured at: {ffmpeg_exe}")
except ImportError:
    print("⚠️ [WARNING] imageio-ffmpeg not found, FFmpeg auto-detection may fail")
except Exception as e:
    print(f"⚠️ [WARNING] FFmpeg configuration failed: {e}")

def assemble_dialogue_v2(script_dto: ScriptDTO, theme_config: ThemeConfig, output_filename: str):
    
    voice_clips = []
    sfx_clips = []
    current_time = 0.0

    print(f"-> Starting Advanced Audio Assembly for topic: {script_dto.topic}")

    try:
        # Validar que tenemos segmentos
        if not script_dto.segments:
            print("❌ ERROR: No segments found in script_dto")
            return None
            
        segments_with_audio = 0
        
        for segment in script_dto.segments:
            if not segment.audio_path:
                print(f"⚠️ WARNING: Segment has no audio_path: {segment}")
                continue
                
            if not os.path.exists(segment.audio_path):
                print(f"❌ ERROR: Audio file does not exist: {segment.audio_path}")
                continue

            try:
                v_clip = AudioFileClip(segment.audio_path).set_start(current_time)
                voice_clips.append(v_clip)
                segments_with_audio += 1
            except Exception as e:
                print(f"❌ ERROR: Failed to load audio segment '{segment.audio_path}': {e}")
                continue

            # 2. Lógica de Highlights (SFX)
            if segment.highlight:
                h_type = segment.highlight.type  # ej: "funny"
                h_context = segment.highlight.context  # ej: "counter"

                resources = getattr(theme_config, 'resources', {})
                options = resources.get(h_type, {}).get(h_context, [])

                if options:
                    try:
                        selected_sfx = random.choice(options)
                        sfx_path = selected_sfx.get('path')

                        if sfx_path and os.path.exists(sfx_path):
                            print(f"   [Highlight] Inserting {selected_sfx['name']} at {current_time:.2f}s")

                            sfx_clip = AudioFileClip(sfx_path).set_start(current_time)
                            sfx_clip = sfx_clip.volumex(0.8)
                            sfx_clips.append(sfx_clip)
                    except Exception as e:
                        print(f"⚠️ WARNING: Failed to add SFX: {e}")

            current_time += segment.duration

        # Verificar que tenemos al menos un clip de audio válido
        if segments_with_audio == 0:
            print("❌ ERROR: No valid audio segments found")
            return None

        # Crear directorio de salida si no existe
        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Crear composición final
        final_composition = CompositeAudioClip(voice_clips + sfx_clips)

        print(f"-> Exporting Master Audio with {len(sfx_clips)} effects...")
        print(f"-> Total segments processed: {segments_with_audio}")
        
        final_composition.write_audiofile(output_filename, fps=44100, logger=None)
        
        # Verificar que el archivo se creó correctamente
        if not os.path.exists(output_filename):
            print(f"❌ ERROR: Failed to create output file: {output_filename}")
            return None
            
        print(f"✅ SUCCESS: Audio assembly completed: {output_filename}")
        return output_filename

    except Exception as e:
        print(f"❌ CRITICAL ERROR in Audio Assembly: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Limpieza de memoria (Crucial en Windows)
        for clip in voice_clips + sfx_clips:
            try:
                clip.close()
            except:
                pass