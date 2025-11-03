import json
from pathlib import Path
from typing import Final

from CreateShorts.Data_Gen.create_audio import assemble_dialogue_pydub
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Data_Gen.create_script_monologue import generate_monolog_script_json
from CreateShorts.Data_Gen.mix_assets import create_final_video
from CreateShorts.Data_Gen.text_to_speach import generate_dialogue_audio
from CreateShorts.Data_Gen.subtitle_generator import SubtitleGenerator, SubtitleConfig
from CreateShorts.Data_Gen.formatter_script import generate_formatter_script_json
from CreateShorts.Prompt_Refinig_Service.refine_base_prompt import refine_base_prompt
from CreateShorts.theme_config import ThemeManager, ThemeConfig

MAX_TIME_LIMIT: Final[int] = 120

# Future update Skyreels.ai
# Create custom configuration (optional)

config = SubtitleConfig(
    fontsize=45,
    font='Arial-Bold',
    color='white',
    stroke_color='black',
    stroke_width=2
)


def get_project_root():
    """Gets the project root path"""
    return Path(__file__).parent.parent


def create_complete_short(topic: str, duration_seconds: int, theme: str = "default", use_template: bool = False,
                          is_monologue: bool = False, context_story: str = ""):
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
        theme_config=theme_config,
        pro_enabled=False
    )

    if theme_config is None:
        print(f"Error: Could not load theme configuration for '{theme}'")
        return

    print(f"-> Theme configuration loaded:")
    print(f"   Video path: {theme_config.video_path}")
    print(f"   Music path: {theme_config.music_path}")
    print(f"   Voice settings: {theme_config.voice_settings}")

    # 1. Generate the script. Here we need to validate if it is a monologue or a debate.
    # If the theme is horror or reddit, we use monologue; otherwise, default (which will change to debate).
    print("-> Generating script...")

    def generate_audio_video(script_json_input: str, output_suffix: str = "_"):
        # 2. Generate audio chunks in memory.
        print("-> Converting script to audio...")
        audio_chunks = generate_dialogue_audio(script_json_input, theme_config)

        if not audio_chunks:
            print("ERROR: Failed to generate audio chunks")
            return

        duration_sum = sum(a.duration for a in audio_chunks)
        duration_second = round(duration_sum)
        print(f"-> Total audio duration: {duration_second} seconds")

        if duration_second > 200:
            print(f"⚠️ Warning: The duration ({duration_second:.2f}s) exceeds 120s")

        # 3. Assemble audio chunks.
        print("-> Assembling audio chunks...")
        temp_audio_path = "temp_dialogue.mp3"
        final_audio_path = assemble_dialogue_pydub(audio_chunks, temp_audio_path)

        if not final_audio_path:
            print("ERROR: Failed to assemble audio")
            return

        try:
            subtitle_gen = SubtitleGenerator(config)
            subtitle_clips = subtitle_gen.create_subtitle_clips(audio_chunks)

            # 5. Create the final video with everything.
            project_root = get_project_root()
            create_final_video(
                voice_path=final_audio_path,
                music_path=theme_config.music_path,
                video_background_path=theme_config.video_path,
                output_path=str(project_root / "output" / f"{topic.replace(' ', '_').lower() + output_suffix}.mp4"),
                duration_sec=duration_second,
                subtitle_clips=subtitle_clips,
                background_volume=theme_config.music_volume
            )
        finally:
            from CreateShorts.Data_Gen.text_to_speach import clean_temp_audio
            clean_temp_audio()

    def get_script_lines_json_str(_part_data: dict) -> str:
        script_lines = _part_data.get('script_lines')
        if script_lines:
            return json.dumps(script_lines)
        return "[]"

    if theme == "story_formatter":
        # --- SERIES LOGIC (Multi-Part) ---

        json_series_str = generate_formatter_script_json(
            time_limit=duration_seconds,
            theme_config=theme_config,
            context_story=context_story
        )

        try:
            # multi_part_scripts_data is a LIST OF Python DICTIONARIES
            multi_part_scripts_data = json.loads(json_series_str)

        except json.JSONDecodeError as e:
            print(f"Fatal error: The JSON returned by Gemini is not valid. {e}")
            return  # Abort

        if not multi_part_scripts_data:
            print("ERROR: Multi-part story segmentation failed.")
            return

        # 2. ITERATE and RE-SERIALIZE for the Factory
        for part_data in multi_part_scripts_data:
            part_number = part_data.get("part_number", 1)

            # 🚨 KEY CORRECTION: We pass ONLY the lines, serialized to a string.
            single_script_json_str = get_script_lines_json_str(part_data)

            # Execute the single video pipeline for this part
            generate_audio_video(
                script_json_input=single_script_json_str,
                output_suffix=f"_part_{part_number}"
            )

    else:
        # --- SINGLE VIDEO LOGIC (Monologue or Debate) ---

        if is_monologue:
            script_json_str = generate_monolog_script_json(
                final_script_prompt=script_prompt,
                time_limit=duration_seconds,
                theme_config=theme_config,
                context=context_story
            )
        else:
            script_json_str = generate_debate_script_json(
                topic=topic,
                time_limit=duration_seconds,
                theme_config=theme_config,
                use_template=use_template,
                context=context_story
            )

        generate_audio_video(script_json_input=script_json_str)


if __name__ == "__main__":
    # _context_story = """
    #  There is a lot of hype lately about AI tools, seems like the new gold fever, but how true is that?.
    #  AI tools definitively are a new way to generate income, either you are a programmer, a content creator, even an accountant if you like, you can use AI tools for everything.
    #  This, however, does not mean you will magically make money at the click of a button, you will need to think hard, work hard or and be creative.
    #  This video, for example, it does uses AI tools, but behind it there is a complicated algorithm that put it all together, there is hard work behind this video.
    #  You might think that is not really that impressive, and you are right, is not. However, the point is that because a lot of hard work behind it, it has been improving rapidly, and now it is capable to create very complex content with minimal effort.
    #  Nothing is for free and just remember that AI tools are not magic, it is your mind what makes the magic.
    #  Use AI tool, nothing wrong with that, but never forget that what you bring to the table is the most important part.
    # """
    _context_story = """
    I use to work for a automatic carwash that originally charged $3 for a wash. One spring we had changed our prices from $3 to $5. I lived in a state that has a lot of winter visitors (old people). The next winter a man comes to purchase a wash during one of the busiest times of the day. He starts to get very angry tells me he is not paying $5 for a wash and demands I reduce the price to $3 for him. After explaining why I cannot do this he gets even more angry. He gets out of his car to yell at me for what felt like forever. At this point there are probably 15-20 cars behind him and no way to get him to leave. The woman behind him gets out of her car and starts yelling at him. I apologize and tell her to please get into her car as I resolved this. She ignores me and continues to bad mouth the guy. He gets angry and goes into his trunk and pulls out his gun. He starts waving it around and threatening the woman, my staff, and me. The woman dives into her car and starts to cry. It isn't my first time having someone pull a gun on me so I calmly tell him to put away his gun since we called the cops. He gets in his car and says he ain't leaving. Within 3 minutes he drives through our gate, drives through a non moving carwash, and makes a run for it. We get his license and when the cops arrive we give the description and plate number. The cop comes back about 45 mins later for more information and tells us that they arrested him and called CPS because he had been drinking and left his 3 yr old grandson at his house, alone, while he went to the carwash. Blew my mind!
    """

    create_complete_short(
        topic="Instant Karma stories about Karen's getting what they deserve",
        duration_seconds=75,
        theme="reddit",
        use_template=False,
        is_monologue=True,
        context_story=_context_story
    )
