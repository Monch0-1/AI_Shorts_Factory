import os
import random
from moviepy.editor import AudioFileClip, CompositeAudioClip
from CreateShorts.Models.script_models import ScriptDTO
from CreateShorts.theme_config import ThemeConfig
from CreateShorts.Services.SFXService import SFXService

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

def assemble_dialogue_v2(script_dto: ScriptDTO, theme_config: ThemeConfig, output_filename: str, include_sfx: bool = True):
    
    voice_clips = []
    sfx_clips = []
    current_time = 0.0
    sfx_service = SFXService()

    print(f"-> Starting Advanced Audio Assembly for topic: {script_dto.topic}")
    if not include_sfx:
        print("   [INFO] SFX processing is DISABLED for this request. Ignoring all highlights.")
        # Ensure that if include_sfx is False, we don't even consider the highlights in the DTO
        for seg in script_dto.segments:
            seg.highlight = None

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
                
                # Increment time BEFORE potentially adding SFX
                current_time += segment.duration

                # 2. Lógica de Highlights (SFX) via Database
                if include_sfx and segment.highlight:
                    h_type = segment.highlight.type
                    h_context = segment.highlight.context
                    h_placement = segment.highlight.placement
                    h_offset = segment.highlight.offset_seconds
                    h_vol_mod = segment.highlight.volume_modifier

                    print(f"   [Highlight] Searching SFX for Type: {h_type}, Context: {h_context}")
                    sfx_path = sfx_service.get_sfx_path(h_type, h_context)

                    if sfx_path and os.path.exists(sfx_path):
                        # Calculate trigger time based on placement
                        # current_time is now at the END of the segment
                        trigger_time = current_time if h_placement == "end" else (current_time - segment.duration)
                        final_start_time = max(0, trigger_time + h_offset)

                        # Calculate volume multiplier from dB modifier
                        import math
                        base_vol = 0.8
                        vol_multiplier = base_vol * (10 ** (h_vol_mod / 20))

                        print(f"   [Highlight] Inserting SFX at {final_start_time:.2f}s (Placement: {h_placement}, Offset: {h_offset}s) | Vol: {vol_multiplier:.2f} | Path: {sfx_path}")

                        try:
                            sfx_clip = AudioFileClip(sfx_path).set_start(final_start_time)
                            sfx_clip = sfx_clip.volumex(vol_multiplier)
                            sfx_clips.append(sfx_clip)
                        except Exception as inner_e:
                            print(f"⚠️ WARNING: Failed to load SFX file '{sfx_path}': {inner_e}")
                    else:
                        print(f"⚠️ SKIP: No SFX found in DB for {h_type}/{h_context}")

            except Exception as e:
                print(f"❌ ERROR: Failed to process segment: {e}")
                continue

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