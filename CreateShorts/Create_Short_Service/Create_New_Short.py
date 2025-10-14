import os
from pathlib import Path

from CreateShorts.Data_Gen.create_audio import assemble_dialogue_pydub
from CreateShorts.Data_Gen.generateScript import generate_script
from CreateShorts.Data_Gen.mix_assets import create_final_video
from CreateShorts.Data_Gen.text_to_speach import generate_dialogue_audio
from CreateShorts.Data_Gen.subtitle_generator import SubtitleGenerator, SubtitleConfig
from create_video import get_absolute_path

DEFAULT_MUSIC_THEME = "2_23_AM.mp3"
HORROR_MUSIC_THEME = "horror.mp3"

# Future update Skyreels.ai
# Crear configuración personalizada (opcional)
config = SubtitleConfig(
    fontsize=45,
    font='Arial-Bold',
    color='white',
    stroke_color='black',
    stroke_width=2
)


def get_music_theme_path(theme: str | None) -> str:
    """
    Determina la ruta del archivo de música basado en el tema.

    Args:
        theme: Tema musical solicitado

    Returns:
        str: Nombre del archivo de música a utilizar
    """
    if theme == "horror":
        return HORROR_MUSIC_THEME
    return DEFAULT_MUSIC_THEME


def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    return Path(__file__).parent.parent

def create_complete_short(topic: str, duration_seconds: int, is_monologue: bool, theme: str = None, theme_context: str = None):
    """Creates a complete short video from start to finish."""
    print(f"-> Starting short video creation for topic: {topic}")
    
    # 1. Generate the script
    print("-> Generating script...")
    script_json = generate_script(topic, duration_seconds, is_monologue, theme_context)
    
    # 2. Generate audio chunks in memory
    print("-> Converting script to audio...")
    audio_chunks = generate_dialogue_audio(script_json)

    if not audio_chunks:
        print("ERROR: Failed to generate audio chunks")
        return

    # Calcular duración total
    duration_sum = sum(a.duration for a in audio_chunks)
    duration_seconds = duration_sum + 0.5  # Buffer
    print(f"-> Duración total del audio: {duration_sum:.2f} segundos")

    # Verificar límite de duración
    if duration_seconds > 120:
        print(f"⚠️ Advertencia: La duración ({duration_seconds:.2f}s) excede 120s")
    
    # 3. Assemble audio chunks
    print("-> Assembling audio chunks...")
    temp_audio_path = "temp_dialogue.mp3"
    final_audio_path = assemble_dialogue_pydub(audio_chunks, temp_audio_path)
    
    if not final_audio_path:
        print("ERROR: Failed to assemble audio")
        return
    
    try:
        # 4. Preparar subtítulos
        subtitle_gen = SubtitleGenerator(config)
        subtitle_clips = subtitle_gen.create_subtitle_clips(audio_chunks)

        # 5. Create final video with everything
        project_root = get_project_root()
        create_final_video(
            voice_path=final_audio_path,
            music_path=str(project_root / "resources" / "audio" / get_music_theme_path(theme)),
            video_background_path=str(project_root / "resources" / "video" / "4.mp4"),
            output_path=str(project_root / "output" / "final_short.mp4"),
            duration_sec=duration_seconds,
            subtitle_clips=subtitle_clips
        )
    finally:
        # Limpieza
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except PermissionError:
                print(f"Temp file was not deleted: {temp_audio_path}")


if __name__ == "__main__":
    background_img = get_absolute_path(".venv/Scripts/background.jpg")
    output_video = get_absolute_path("final_short.mp4")
    
    create_complete_short(
        topic="The unsettling silence of a remote cabin, where things keep moving when you're not looking.",
        duration_seconds=60,
        is_monologue=True,
        theme= "horror",
        theme_context=f"""The story is about extreme isolation and psychological horror. 
        A solitary man, deeply obsessed with his recently deceased mother, 
        lives in a decaying farmhouse. Following his mother's death, he sealed her room off, 
        leaving the rest of the house to rot. The core horror is that the man didn't just leave the house; 
        he started filling it with objects made from things he found—things that looked like furniture, 
        clothing, or bowls, but were clearly fabricated from human remains. 
        The discovery of these household items is the central horrifying event. 
        Focus on the sensory details of the house: the dust, the silence, the smell of decay, 
        and the chilling realization that ordinary objects have been twisted into something macabre. 
        The climax should be the discovery of a 'trophy' item made of human skin that suggests a deeper, 
        terrifying obsession with identity."""
    )