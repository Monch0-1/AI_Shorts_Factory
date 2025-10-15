from pathlib import Path

from CreateShorts.Data_Gen.create_audio import assemble_dialogue_pydub
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Data_Gen.create_script_monologue import generate_monolog_script_json
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

def create_complete_short(topic: str, duration_seconds: int, theme: str = "default", use_template: bool = False, is_monologue: bool = False, context_story: str = ""):
    """
    Creates a complete short video from start to finish.
    
    Args:
        topic (str): Topic for the video content
        duration_seconds (int): Desired duration in seconds
        theme (str): Theme name to use for video configuration
        use_template (bool): Whether to use a template
        :param context_story:
        :param topic:
        :param duration_seconds:
        :param theme:
        :param use_template:
        :param is_monologue:
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

    # 1. Generate the script here we need to validate if is it monologue or debate
    # if theme is horror or reddit, then we use monologue, else default (will change to debate).
    print("-> Generating script...")
    if is_monologue:
        script_json = generate_monolog_script_json(
            topic=topic,
            time_limit=duration_seconds,
            theme_config=theme_config,
        )

    else:
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
    duration_seconds = round(duration_sum)  # Redondear en lugar de añadir buffer
    print(f"-> Duración total del audio: {duration_seconds} segundos")

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

    _context_story = """I I was applying for a simple marketing job after college. The interviewer, a man named 'Dave,' emailed saying, 'Meet me at The Corner Cafe at 6 PM.' I thought, 'Wow, very casual office culture!' I got there, Dave was at a tiny table, candlelit, with jazz music playing. He ordered two glasses of wine. I spent ten minutes talking about my 'long-term relationship goals' with the company and how 'open I am to new experiences.' He kept smiling weirdly. Finally, he said, 'Wait, you're looking for a job? I thought you were Nancy from the dating app.' I realized I was one table off. I had interviewed a random stranger about my career goals over Merlot. I just said, 'Well, I'm great under pressure,' grabbed my things, and ran"""
    
    create_complete_short(
        topic="The time I confused a job interview with a blind date.",
        duration_seconds=120,
        theme="reddit",
        use_template=True,
        is_monologue=True,
        context_story=_context_story
    )