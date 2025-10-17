from pathlib import Path
from typing import Final

from CreateShorts.Data_Gen.create_audio import assemble_dialogue_pydub
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Data_Gen.create_script_monologue import generate_monolog_script_json
from CreateShorts.Data_Gen.mix_assets import create_final_video
from CreateShorts.Data_Gen.text_to_speach import generate_dialogue_audio
from CreateShorts.Data_Gen.subtitle_generator import SubtitleGenerator, SubtitleConfig
from CreateShorts.Prompt_Refinig_Service.refine_base_prompt import refine_base_prompt
from CreateShorts.theme_config import ThemeManager, ThemeConfig

MAX_TIME_LIMIT: Final[int] = 120
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

    # Load theme config
    theme_manager = ThemeManager()
    theme_config = theme_manager.get_theme_config(theme)

    script_prompt = refine_base_prompt(
        base_topic_or_idea=topic,
        theme_config=theme_config
    )
    
    if theme_config is None:
        print(f"Error: No se pudo cargar la configuración del tema '{theme}'")
        return
        
    print(f"-> Theme configuration loaded:")
    print(f"   Video path: {theme_config.video_path}")
    print(f"   Music path: {theme_config.music_path}")
    print(f"   Voice settings: {theme_config.voice_settings}")

    # 1. Generate the script here we need to validate if is it monologue or debate
    # if theme is horror or reddit, then we use monologue, else default (will change to debate).
    print("-> Generating script...")
    if is_monologue:
        script_json = generate_monolog_script_json(
            final_script_prompt=script_prompt,
            time_limit=duration_seconds,
            theme_config=theme_config,
            context=context_story
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
        from CreateShorts.Data_Gen.text_to_speach import clean_temp_audio
        clean_temp_audio()


if __name__ == "__main__":

    _context_story = """
    So, I work at a restaurant, and the other night we had this sweet elderly couple come in for dinner. They finished their meal, and the gentleman excused himself to the restroom. No big deal, right? Well, he was in there for like, and hour until his wife finally went in to retrieve him. Fast forward a few hours—now we're closing up, and it’s my turn to clean the bathroom.
    I walk in, and oh my gosh, the horror. The toilet was clogged to the brim with poop, the trash can was overflowing with paper towels smeared with—you guessed it—poop, and there was poop on the floor. And the smell. Oh, the smell. I’m telling you, I couldn't even.
    So, my coworker Dan (bless his soul) took one for the team. He unclogged the toilet, wiped up the poop on the floor, and I had to tackle the trash can. I pulled out the bag, and lo and behold, there was a rogue turd hiding underneath the trash bag in the trash can. I don't even want to know how that happened.
    Even after Dan wiped down the walls with bleach, the bathroom reeked for days. It’s only just starting to smell normal, but it was so bad you could smell it in the dining room. One of the cooks has dubbed this guy “The Phantom Shitter.” So yeah, that was our night. Hope someone finds this as hilarious as we did (after the trauma subsided, of course).
    """
    
    create_complete_short(
        topic="The Phantom Shitter that my coworker and I had to clean up after",
        duration_seconds=60,
        theme="reddit",
        use_template=True,
        is_monologue=True,
        context_story=_context_story
    )