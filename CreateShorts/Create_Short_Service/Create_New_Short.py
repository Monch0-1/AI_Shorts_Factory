from pathlib import Path

from CreateShorts.Data_Gen.create_audio import assemble_dialogue_pydub
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Data_Gen.mix_assets import create_final_video
from CreateShorts.Data_Gen.text_to_speach import generate_dialogue_audio
from CreateShorts.Data_Gen.subtitle_generator import SubtitleGenerator, SubtitleConfig
from create_video import get_absolute_path
from CreateShorts.theme_config import ThemeManager, ThemeConfig

# Future update Skyreels.ai
# Crear configuración personalizada (opcional)
config = SubtitleConfig(
    fontsize=45,
    font='Arial-Bold',
    color='white',
    stroke_color='black',
    stroke_width=2
)

def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    return Path(__file__).parent.parent

def create_complete_short(topic: str, duration_seconds: int, theme: str = "default", use_template: bool = False):
    """
    Creates a complete short video from start to finish.
    
    Args:
        topic (str): Topic for the video content
        duration_seconds (int): Desired duration in seconds
        theme (str): Theme name to use for video configuration
        use_template (bool): Whether to use a template
    """

    print(f"-> Starting short video creation for topic: {topic}")
    print(f"-> Using theme: {theme}")

    # Cargar configuración del tema
    theme_manager = ThemeManager()
    theme_config = theme_manager.get_theme_config(theme)
    
    if theme_config is None:
        print(f"Error: No se pudo cargar la configuración del tema '{theme}'")
        return
        
    print(f"-> Configuración del tema cargada:")
    print(f"   Video path: {theme_config.video_path}")
    print(f"   Music path: {theme_config.music_path}")
    print(f"   Voice settings: {theme_config.voice_settings}")

    # 1. Generate the script
    print("-> Generating script...")
    script_json = generate_debate_script_json(
        topic=topic,
        time_limit=duration_seconds,
        theme_config=theme_config,
        use_template=use_template
    )

    # 2. Generate audio chunks in memory
    print("-> Converting script to audio...")
    audio_chunks = generate_dialogue_audio(script_json, theme_config)

    if not audio_chunks:
        print("ERROR: Failed to generate audio chunks")
        return

    # Calcular duración total
    duration_sum = sum(a.duration for a in audio_chunks)
    duration_seconds = duration_sum + 0.5  # Buffer
    print(f"-> Duración total del audio: {duration_sum:.2f} segundos")

    # Verificar límite de duración
    if duration_seconds > 200:
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
            music_path=theme_config.music_path,
            video_background_path=theme_config.video_path,
            output_path=str(project_root / "output" / f"{topic.replace(' ', '_').lower()}.mp4"),
            duration_sec=duration_seconds,
            subtitle_clips=subtitle_clips,
            background_volume=theme_config.music_volume
        )
    finally:
        # Limpiar archivos temporales
        from CreateShorts.Data_Gen.text_to_speach import clean_temp_audio
        clean_temp_audio()


if __name__ == "__main__":
    background_img = get_absolute_path(".venv/Scripts/background.jpg")
    output_video = get_absolute_path("final_short.mp4")
    
    create_complete_short(
        topic="best smartphones 2025",
        duration_seconds=100,
        theme="default",
        use_template=True,
    )