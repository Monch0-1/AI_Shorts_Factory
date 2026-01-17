import json
import random
from pathlib import Path
from typing import Final, Optional, Union
from dataclasses import dataclass

from CreateShorts.Data_Gen.create_audio import assemble_dialogue_pydub
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Data_Gen.create_script_monologue import generate_monolog_script_json
from CreateShorts.Data_Gen.mix_assets import create_final_video
from CreateShorts.Data_Gen.text_to_speach import generate_dialogue_audio, clean_temp_audio
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

@dataclass
class VideoRequest:
    """
    Encapsulates the parameters required to create a short video.
    Acts as a Data Transfer Object (DTO) for video generation requests.
    """
    topic: str
    duration_seconds: int
    theme: str = "default"
    use_template: bool = False
    is_monologue: bool = False
    context_story: str = ""
    video_index: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoRequest':
        """Creates a VideoRequest instance from a dictionary, handling defaults."""
        return cls(
            topic=data.get("topic", "Untitled"),
            duration_seconds=data.get("duration_seconds", 60),
            theme=data.get("theme", "default"),
            use_template=data.get("use_template", False),
            is_monologue=data.get("is_monologue", False),
            context_story=data.get("context_story", ""),
            video_index=data.get("video_index")
        )


def get_project_root():
    """Gets the project root path"""
    return Path(__file__).parent.parent


def _select_video_resource(theme_config: ThemeConfig, video_index: Optional[int]) -> str:
    """Selects the background video path based on index or random choice."""
    if not theme_config.video_paths:
        print("   WARNING: No video paths found in theme config.")
        return ""

    if video_index is not None and 0 <= video_index < len(theme_config.video_paths):
        selected = theme_config.video_paths[video_index]
        print(f"   Video path (Selected {video_index}): {selected}")
        return selected

    selected = random.choice(theme_config.video_paths)
    print(f"   Video path (Random): {selected}")
    return selected


def _run_av_pipeline(script_json: str, topic: str, theme_config: ThemeConfig, video_path: str, output_suffix: str = "_"):
    """
    Executes the Audio/Video generation pipeline:
    TTS -> Audio Assembly -> Subtitles -> Final Video Rendering.
    """
    print("-> Converting script to audio...")
    audio_chunks = generate_dialogue_audio(script_json, theme_config)

    if not audio_chunks:
        print("ERROR: Failed to generate audio chunks")
        return

    duration_sum = sum(a.duration for a in audio_chunks)
    duration_second = round(duration_sum)
    print(f"-> Total audio duration: {duration_second} seconds")

    if duration_second > 200:
        print(f"⚠️ Warning: The duration ({duration_second:.2f}s) exceeds 120s")

    # Assembling audio chunks
    print("-> Assembling audio chunks...")
    temp_audio_path = "temp_dialogue.mp3"
    final_audio_path = assemble_dialogue_pydub(audio_chunks, temp_audio_path)

    if not final_audio_path:
        print("ERROR: Failed to assemble audio")
        return

    try:
        subtitle_gen = SubtitleGenerator(config)
        subtitle_clips = subtitle_gen.create_subtitle_clips(audio_chunks)

        # Create the final video
        project_root = get_project_root()
        create_final_video(
            voice_path=final_audio_path,
            music_path=theme_config.music_path,
            video_background_path=video_path,
            output_path=str(project_root / "output" / f"{topic.replace(' ', '_').lower() + output_suffix}.mp4"),
            duration_sec=duration_second,
            subtitle_clips=subtitle_clips,
            background_volume=theme_config.music_volume
        )
    finally:
        clean_temp_audio()


def _handle_story_series_flow(request: VideoRequest, theme_config: ThemeConfig, video_path: str):
    """Handles the generation of multi-part story videos."""
    json_series_str = generate_formatter_script_json(
        time_limit=request.duration_seconds,
        theme_config=theme_config,
        context_story=request.context_story
    )

    try:
        multi_part_scripts_data = json.loads(json_series_str)
    except json.JSONDecodeError as e:
        print(f"Fatal error: The JSON returned by Gemini is not valid. {e}")
        return

    if not multi_part_scripts_data:
        print("ERROR: Multi-part story segmentation failed.")
        return

    for part_data in multi_part_scripts_data:
        part_number = part_data.get("part_number", 1)
        script_lines = part_data.get('script_lines', [])
        single_script_json_str = json.dumps(script_lines) if script_lines else "[]"

        _run_av_pipeline(single_script_json_str, request.topic, theme_config, video_path, output_suffix=f"_part_{part_number}")


def _handle_standard_flow(request: VideoRequest, theme_config: ThemeConfig, video_path: str):
    """Handles the generation of standard Monologue or Debate videos."""
    if request.is_monologue:
        final_prompt = refine_base_prompt(request.topic, theme_config, False)
        script_json_str = generate_monolog_script_json(
            final_script_prompt=final_prompt,
            time_limit=request.duration_seconds,
            theme_config=theme_config,
            context=request.context_story
        )
    else:
        script_json_str = generate_debate_script_json(
            topic=request.topic,
            time_limit=request.duration_seconds,
            theme_config=theme_config,
            use_template=request.use_template,
            context=request.context_story
        )

    _run_av_pipeline(script_json_str, request.topic, theme_config, video_path)


def create_complete_short(topic: str, duration_seconds: int, theme: str = "default", use_template: bool = False,
                          is_monologue: bool = False, context_story: str = "", video_index: int = None):
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
        :param video_index: Optional index to select a specific video from the theme's list.
        :param use_template:
        :param is_monologue:
    """

    # Structure input data into a Request Object
    request = VideoRequest(
        topic=topic,
        duration_seconds=duration_seconds,
        theme=theme,
        use_template=use_template,
        is_monologue=is_monologue,
        context_story=context_story,
        video_index=video_index
    )

    print(f"-> Starting short video creation for topic: {request.topic}")
    print(f"-> Using theme: {request.theme}")

    # Load theme config
    theme_manager = ThemeManager()
    theme_config = theme_manager.get_theme_config(request.theme)

    if theme_config is None:
        print(f"Error: Could not load theme configuration for '{request.theme}'")
        return

    print(f"-> Theme configuration loaded:")
    video_path = _select_video_resource(theme_config, request.video_index)
    print(f"   Music path: {theme_config.music_path}")
    print(f"   Voice settings: {theme_config.voice_settings}")

    print("-> Generating script...")
    if request.theme == "story_formatter":
        _handle_story_series_flow(request, theme_config, video_path)
    else:
        _handle_standard_flow(request, theme_config, video_path)


def create_short_from_json(request_data: Union[dict, VideoRequest]):
    """
    Wrapper function that processes a video request.
    Accepts either a dictionary (JSON) or a VideoRequest object.
    """
    if not request_data:
        print("Error: No request data provided.")
        return

    # Convert dict to VideoRequest if necessary
    if isinstance(request_data, dict):
        video_request = VideoRequest.from_dict(request_data)
    elif isinstance(request_data, VideoRequest):
        video_request = request_data
    else:
        print("Error: Invalid data type. Expected dict or VideoRequest.")
        return

    # Extract values from the encapsulated object
    create_complete_short(
        topic=video_request.topic,
        duration_seconds=video_request.duration_seconds,
        theme=video_request.theme,
        use_template=video_request.use_template,
        is_monologue=video_request.is_monologue,
        context_story=video_request.context_story,
        video_index=video_request.video_index
    )


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
    _context_story = """This video (around 5 minutes) would debunk five super common misconceptions that most people have 
    heard or even still believe. It’s relatable, surprising, and sparks curiosity—perfect for keeping viewers hooked in a short format.
    
    INSTRUCTIONS: 
    Structure Outline
1. 	Intro (30 seconds)
• 	Hook: “Think you know the truth about these everyday facts? You might be wrong…”
• 	Quick montage of the myths to tease what’s coming.
2. 	Top 5 Countdown (4 minutes)
• 	#5: Goldfish Memory – They don’t just have 3-second memories; studies show they can remember things for months.
• 	#4: Cracking Knuckles Causes Arthritis – Research shows no direct link; it’s mostly harmless.
• 	#3: Humans Only Use 10% of Their Brain – Neuroscience proves we use nearly all parts of our brain, just not all at once.
• 	#2: Sugar Makes Kids Hyper – Multiple studies show no consistent evidence; excitement is usually situational.
• 	#1: The Great Wall of China Visible from Space – Astronauts confirm it’s not easily visible without aid; it blends with the landscape.
2. 	Each myth gets about 40–50 seconds with visuals, playful debunking, and maybe a quick animation or stock footage.
3. 	Outro (30 seconds)
• 	Wrap-up: “So next time someone repeats these myths, you’ll know the truth!”
• 	Call-to-action: “Which myth fooled you the longest? Share below!”

This concept mixes relatable everyday beliefs with surprising corrections, making it both fun and informative.
    
    """


    # Example using the VideoRequest Data Class
    video_request = VideoRequest(
        topic="5 Everyday Myths You Still Believe (But Aren’t True)",
        duration_seconds=80,
        theme="Default",
        use_template=True,
        is_monologue=False,
        context_story=_context_story,
        # video_index=0  # Optional
    )

    create_short_from_json(video_request)
