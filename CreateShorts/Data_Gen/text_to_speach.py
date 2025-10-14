import json
import os
from dataclasses import dataclass
from moviepy.editor import AudioFileClip
from elevenlabs.client import ElevenLabs
from CreateShorts.Create_Short_Service.loadEnvData import load_env_data

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
    "Tina": "CCYamdRMfatPAgJsW7xb",
    "Survivor": "CCYamdRMfatPAgJsW7xb"
}
MODEL_ID = "eleven_multilingual_v2"
client = load_env_data(ElevenLabs, "ELEVEN_API_KEY")
TEMP_DIR = os.path.join("PythonProject", "CreateShorts", "resources", "audio", "temp_audio")

def generate_dialogue_audio(json_script_str: str) -> list[AudioChunkInfo]:
    """Genera y guarda chunks de audio para cada línea en el diálogo JSON.

    Args:
        json_script_str: Cadena JSON que contiene el script del diálogo

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

    for i, turn in enumerate(script_data):
        speaker_name = turn['speaker']
        line_text = turn['line']
        voice_id = VOICE_IDS.get(speaker_name)

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