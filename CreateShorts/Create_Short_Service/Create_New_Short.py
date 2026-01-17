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

    # script_prompt = refine_base_prompt(
    #     base_topic_or_idea=topic,
    #     theme_config=theme_config,
    #     pro_enabled=False
    # )

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
                final_script_prompt=refine_base_prompt(
                    topic,
                    theme_config,
                    False
                ),
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
#     _context_story = """
#      Am I the a-hole For intentionally scary my neighbours kids
#
# My bedroom window faces the front yard. During the day I have the blinds half open, enough to let in some light and sunshine for my cats. From the street and even the front yard, it’s not possible to see clearly into my bedroom. Because of this, I do often walk through my bedroom in my underwear or just partly dressed to get to the bathroom. I don’t risk walking around naked though.
#
# Recently, my neighbour’s twin kids, both male and I’m guessing around 7 years old, have started looking in my bedroom window. I don’t just mean standing by the window in my yard, I’m talking faces and hands completely pressed up against the window looking in.
#
# I assume this started with them looking at my cats, but now I think they consider it some type of game with me. If they see me, they run back home laughing. I have caught them outside on a number of occasions and asked them directly not to do this, but again they just run away laughing like it’s a game.
#
# I’ve also spoken to their parents multiple times, and they refuse to do anything about it. The response I got was “they’re just kids being kids” and “if you don’t want someone looking in your window just keep it closed”. I think that teaching your kids that it’s ok to go onto someone’s property and peek in their window is kinda fucked up. I know they’re only young, but I still feel like my privacy is being invaded.
#
# This has been going on almost daily for months now, until last week. I walked in my bedroom and heard the kids outside playing, then spotted the terrifying demon like mask that my boyfriend wore to a Halloween party the night before. So I got an idea.
#
# I stood next to my window wearing the mask for almost 20 minutes. Finally I heard the footsteps approaching and waited until both kids had their noses pressed up against the window. At that moment I jumped out, mask right at their eye level, and let out the deepest and loudest roar I possibly could.
#
# In all the years living next to these neighbours I’ve never heard them scream as loudly as they did when they saw me. They ran home screaming and crying, and just minutes later their mother was at my door, calling me a monster for scaring her children. I simply told her that I do what I want in my own house, and if her kids don’t want to see that they should stay away from my window.
#
# It’s been a week now and I’m glad to say the kids have not even stepped foot on my front lawn. Not sure if it’s because they’re traumatised, or the parents have just told them not to do it anymore. Either way, I’m happy.
#
# I felt justified at the time, but everyone I’ve told has said that I took it too far for such young children. So I don’t know, Am I the a-hole?


    # """
    _context_story = """This short video (around 5 minutes) would explore five common, relatable items or habits we all encounter daily, but with surprising or quirky backstories. The tone should be light, fun, and sprinkled with interesting facts that make viewers say, 
    “Wait, really?!” Perfect for keeping attention in a short format.
    
    INSTRUCTIONS: 
    Structure Outline
1. 	Intro 
• 	Quick hook: “We use these things every day, but their origins are stranger than you think…”
• 	Energetic visuals and upbeat music to set the mood.
2. 	Top 5 Countdown 
• 	#5: The Toothbrush – Ancient civilizations used twigs and frayed sticks long before bristles.
• 	#4: Jeans – Originally designed as durable workwear for miners, now a global fashion staple.
• 	#3: Coffee – Legend says it was discovered after goats in Ethiopia got hyper from eating coffee berries.
• 	#2: Umbrella – First used in ancient China not for rain, but as a symbol of status and shade.
• 	#1: High-Fives – The gesture only became popular in the late 1970s, thanks to baseball players.
2. 	Each item gets about 40–50 seconds with visuals, fun facts, and maybe a playful animation or stock footage.
3. 	Outro 
• 	Wrap-up: “So next time you sip coffee or throw on jeans, remember their weird beginnings!”
• 	Call-to-action: “Which origin story surprised you the most? Comment below!”
    
    """


    create_complete_short(
        topic="Top 5 Everyday Things You Didn’t Know Had Weird Origins",
        duration_seconds=800,
        theme="Default",
        use_template=True,
        is_monologue=False,
        context_story=_context_story
    )
