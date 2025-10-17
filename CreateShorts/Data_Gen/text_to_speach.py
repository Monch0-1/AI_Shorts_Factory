import json
import os
from dataclasses import dataclass
from moviepy.editor import AudioFileClip
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from CreateShorts.Create_Short_Service.loadEnvData import load_env_data
from CreateShorts.theme_config import ThemeConfig
from CreateShorts.Data_Gen.eleven_labs_voice_settings_config import ElevenLabsVoiceSettings
from typing import Optional


@dataclass
class AudioChunkInfo:
    """Clase para almacenar información sobre cada chunk de audio"""
    content: bytes
    duration: float
    speaker: str
    text: str
    filename: str

VOICE_IDS = {
    "Nina": "kv829HVkmQ1fOJX1MjSN",
    "Tina": "GwUCiXil6qHfygWUJEwS",
    "Anon": "GwUCiXil6qHfygWUJEwS",
}
MODEL_ID = "eleven_multilingual_v2"
client = load_env_data(ElevenLabs, "ELEVEN_API_KEY")
TEMP_DIR = os.path.join("PythonProject", "CreateShorts", "resources", "audio", "temp_audio")


def get_elevenlabs_settings(settings_data: Optional[ElevenLabsVoiceSettings]) -> Optional[VoiceSettings]:
    """
    Convierte la dataclass custom en el objeto VoiceSettings nativo de ElevenLabs.
    """
    if settings_data is None:
        # Valores por defecto si no hay configuración
        return VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            speed=1.0,
            use_speaker_boost=True
        )

    # Crear el objeto VoiceSettings con los valores de la configuración
    return VoiceSettings(
        stability=settings_data.stability if settings_data.stability is not None else 0.5,
        similarity_boost=settings_data.similarity_boost if settings_data.similarity_boost is not None else 0.75,
        style=settings_data.style if settings_data.style is not None else 0.0,
        speed=settings_data.speed if settings_data.speed is not None else 1.0,
        use_speaker_boost=settings_data.use_speaker_boost if settings_data.use_speaker_boost is not None else True
    )

def generate_dialogue_audio(json_script_str: str, theme_config: Optional[ThemeConfig] = None) -> list[AudioChunkInfo]:
    """Genera y guarda chunks de audio para cada línea en el diálogo JSON.

    Args:
        json_script_str (str): Cadena JSON que contiene el script del diálogo
        theme_config (Optional[ThemeConfig]): Configuración del tema que incluye voice_settings

    Returns:
        list[AudioChunkInfo]: Lista de información de chunks de audio
    """

    if client is None:
        return []

    os.makedirs(TEMP_DIR, exist_ok=True)

    try:
        script_data = json.loads(json_script_str)
    except json.JSONDecodeError as e:
        print(f"ERROR: No se pudo decodificar el JSON del script. {e}")
        return []

    audio_chunks_info = []
    voice_settings_obj = get_elevenlabs_settings(theme_config.voice_settings)

    for i, turn in enumerate(script_data):
        speaker_name = turn['speaker']
        line_text = turn['line']
        voice_id = VOICE_IDS[speaker_name] if speaker_name in VOICE_IDS else VOICE_IDS["Anon"]

        if not voice_id:
            print(f"ERROR: No se encontró Voice ID para el hablante: {speaker_name}")
            return []

        try:
            # Obtener el audio desde la API
            audio_generator = client.text_to_speech.convert(
                text=line_text,
                voice_id=voice_id,
                model_id=MODEL_ID,
                output_format="mp3_44100_128",
                voice_settings=voice_settings_obj
            )

            # Convertir el generador a bytes
            audio_content = b''.join(chunk for chunk in audio_generator)

            # Guardar el chunk en un archivo
            chunk_filename = f'chunk_{i}_{speaker_name}.mp3'
            chunk_path = os.path.join(TEMP_DIR, chunk_filename)
            with open(chunk_path, 'wb') as f:
                f.write(audio_content)

            # Obtener la duración usando moviepy
            with AudioFileClip(chunk_path) as audio_clip:
                duration = audio_clip.duration

            # Crear objeto AudioChunkInfo
            chunk_info = AudioChunkInfo(
                content=audio_content,
                duration=duration,
                speaker=speaker_name,
                text=line_text,
                filename=chunk_filename
            )
            
            audio_chunks_info.append(chunk_info)

        except Exception as e:
            print(f"ERROR generando audio para '{speaker_name}': {e}")
            return []

    print(f"-> Generación de audio completada. Se crearon {len(audio_chunks_info)} chunks.")
    print(f"-> Los chunks de audio se guardaron en: {TEMP_DIR}")
    
    # Imprimir información de duración para cada chunk
    #test1
    #tete
    for chunk in audio_chunks_info:
        print(f"-> Chunk: {chunk.filename}")
        print(f"   Duración: {chunk.duration:.2f} segundos")
        print(f"   Hablante: {chunk.speaker}")
        print(f"   Texto: {chunk.text}")

    return audio_chunks_info

def clean_temp_audio():
    """
    Limpia todos los archivos de audio temporales en el directorio TEMP_DIR.
    """
    try:
        if os.path.exists(TEMP_DIR):
            # Obtener lista de archivos en el directorio
            files = os.listdir(TEMP_DIR)
            
            # Eliminar cada archivo
            for file in files:
                file_path = os.path.join(TEMP_DIR, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"-> Archivo eliminado: {file}")
                except Exception as e:
                    print(f"Error al eliminar {file}: {e}")
            
            print("-> Limpieza de archivos temporales completada")
        else:
            print(f"-> El directorio {TEMP_DIR} no existe")
            
    except Exception as e:
        print(f"Error durante la limpieza: {e}")