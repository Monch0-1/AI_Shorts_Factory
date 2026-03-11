import os
from moviepy.editor import AudioFileClip
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from CreateShorts.loadEnvData import load_env_data
from CreateShorts.theme_config import ThemeConfig
from CreateShorts.Data_Gen.eleven_labs_voice_settings_config import ElevenLabsVoiceSettings
from CreateShorts.Models.script_models import ScriptDTO
from typing import Optional
import uuid


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

VOICE_IDS = {
    "Nina": "kv829HVkmQ1fOJX1MjSN",
    "Tina": "GwUCiXil6qHfygWUJEwS",
    "Anon": "GwUCiXil6qHfygWUJEwS",
    "Narrator_Female": "NDTYOmYEjbDIVCKB35i3",
    "Anon": "PIGsltMj3gFMR34aFDI3"
}
MODEL_ID = "eleven_multilingual_v2"
client = load_env_data(ElevenLabs, "ELEVEN_API_KEY")
TEMP_DIR = os.path.join("MockAudioFiles", "CreateShorts", "resources", "audio", "temp_audio")


def get_elevenlabs_settings(settings_data: Optional[ElevenLabsVoiceSettings]) -> Optional[VoiceSettings]:
    """
    Converts the custom dataclass into the native ElevenLabs VoiceSettings object.
    """
    if settings_data is None:
        # Default values if there is no configuration
        return VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            speed=1.0,
            use_speaker_boost=True
        )

    # Create the VoiceSettings object with the configuration values
    return VoiceSettings(
        stability=settings_data.stability if settings_data.stability is not None else 0.5,
        similarity_boost=settings_data.similarity_boost if settings_data.similarity_boost is not None else 0.75,
        style=settings_data.style if settings_data.style is not None else 0.0,
        speed=settings_data.speed if settings_data.speed is not None else 1.0,
        use_speaker_boost=settings_data.use_speaker_boost if settings_data.use_speaker_boost is not None else True
    )


def generate_script_audio_v2(script: ScriptDTO, theme_config: ThemeConfig) -> ScriptDTO:
    """
    Versión corregida: Procesa el ScriptDTO y lo actualiza con
    metadata física (duración y paths) usando los nombres de campo correctos.
    """
    if client is None:
        return script

    os.makedirs(TEMP_DIR, exist_ok=True)
    voice_settings_obj = get_elevenlabs_settings(theme_config.voice_settings)

    # Nota: Usamos enumerate por si el 'index' del DTO no viene o es inconsistente
    for i, segment in enumerate(script.segments):
        # 1. Determinar Voz (Usando .speaker)
        voice_id = VOICE_IDS.get(segment.speaker, VOICE_IDS["Anon"])

        try:
            print(f"-> Generating audio for segment {i} ({segment.speaker})...")

            # 2. Llamada a ElevenLabs (Usando .line)
            audio_generator = client.text_to_speech.convert(
                text=segment.line,
                voice_id=voice_id,
                model_id=MODEL_ID,
                output_format="mp3_44100_128",
                voice_settings=voice_settings_obj
            )

            audio_content = b''.join(chunk for chunk in audio_generator)

            # 3. Guardar con UUID
            file_name = f"seg_{i}_{uuid.uuid4().hex[:6]}.mp3"
            chunk_path = os.path.join(TEMP_DIR, file_name)

            with open(chunk_path, 'wb') as f:
                f.write(audio_content)

            # 4. CAPTURAR DURACIÓN Y ACTUALIZAR EL DTO
            with AudioFileClip(chunk_path) as audio_clip:
                segment.duration = audio_clip.duration

            segment.audio_path = chunk_path

            # Print corregido para no usar .character
            print(f"   [OK] {segment.duration:.2f}s | Path: {file_name}")

        except Exception as e:
            print(f"❌ ERROR en segmento {i}: {e}")
            continue

    return script

# def generate_dialogue_audio(json_script_str: str, theme_config: Optional[ThemeConfig] = None) -> list[AudioChunkInfo]:
#     """Generates and saves audio chunks for each line in the JSON dialogue.
#
#     Args:
#         json_script_str (str): JSON string containing the dialogue script
#         theme_config (Optional[ThemeConfig]): Theme configuration that includes voice_settings
#
#     Returns:
#         list[AudioChunkInfo]: List of audio chunk information
#     """
#
#     if client is None:
#         return []
#
#     os.makedirs(TEMP_DIR, exist_ok=True)
#
#     try:
#         script_data = json.loads(json_script_str)
#     except json.JSONDecodeError as e:
#         print(f"ERROR: Could not decode the script JSON. {e}")
#         return []
#
#     audio_chunks_info = []
#     voice_settings_obj = get_elevenlabs_settings(theme_config.voice_settings)
#
#     for i, turn in enumerate(script_data):
#         speaker_name = turn['speaker']
#         line_text = turn['line']
#         voice_id = VOICE_IDS[speaker_name] if speaker_name in VOICE_IDS else VOICE_IDS["Anon"]
#
#         if not voice_id:
#             print(f"ERROR: Voice ID not found for speaker: {speaker_name}")
#             return []
#
#         try:
#             # Get audio from the API
#             audio_generator = client.text_to_speech.convert(
#                 text=line_text,
#                 voice_id=voice_id,
#                 model_id=MODEL_ID,
#                 output_format="mp3_44100_128",
#                 voice_settings=voice_settings_obj
#             )
#
#             # Convert the generator to bytes
#             audio_content = b''.join(chunk for chunk in audio_generator)
#
#             # Save the chunk to a file
#             chunk_filename = f'chunk_{i}_{speaker_name}.mp3'
#             chunk_path = os.path.join(TEMP_DIR, chunk_filename)
#             with open(chunk_path, 'wb') as f:
#                 f.write(audio_content)
#
#             # Get duration using moviepy
#             with AudioFileClip(chunk_path) as audio_clip:
#                 duration = audio_clip.duration
#
#             # Create AudioChunkInfo object
#             chunk_info = AudioChunkInfo(
#                 content=audio_content,
#                 duration=duration,
#                 speaker=speaker_name,
#                 text=line_text,
#                 filename=chunk_filename
#             )
#
#             audio_chunks_info.append(chunk_info)
#
#         except Exception as e:
#             print(f"ERROR generating audio for '{speaker_name}': {e}")
#             return []

    # print(f"-> Audio generation completed. {len(audio_chunks_info)} chunks were created.")
    # print(f"-> Audio chunks were saved in: {TEMP_DIR}")
    #
    # # Print duration information for each chunk
    # #test1
    # #tete
    # for chunk in audio_chunks_info:
    #     print(f"-> Chunk: {chunk.filename}")
    #     print(f"   Duration: {chunk.duration:.2f} seconds")
    #     print(f"   Speaker: {chunk.speaker}")
    #     print(f"   Text: {chunk.text}")
    #
    # return audio_chunks_info

def clean_temp_audio():
    """
    Cleans all temporary audio files in the TEMP_DIR directory.
    """
    try:
        if os.path.exists(TEMP_DIR):
            # Get list of files in the directory
            files = os.listdir(TEMP_DIR)
            
            # Delete each file
            for file in files:
                file_path = os.path.join(TEMP_DIR, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"-> File deleted: {file}")
                except Exception as e:
                    print(f"Error deleting {file}: {e}")
            
            print("-> Cleanup of temporary files completed")
        else:
            print(f"-> The directory {TEMP_DIR} does not exist")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")