import json
import random
from pathlib import Path
from typing import Final, Optional, Union
from dataclasses import dataclass

from CreateShorts.Create_Short_Service.Models.script_models import ScriptDTO
from CreateShorts.Data_Gen.create_audio import assemble_dialogue_v2
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Data_Gen.create_script_monologue import generate_monolog_script_json
from CreateShorts.Data_Gen.mix_assets import create_final_video
from CreateShorts.Data_Gen.text_to_speach import clean_temp_audio, generate_script_audio_v2
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

def parse_script_to_dto(topic: str, script_json_str: str) -> Optional[ScriptDTO]:
    try:
        data = json.loads(script_json_str)
        if isinstance(data, list):
            return ScriptDTO(topic=topic, segments=data)
        return ScriptDTO(**data)
    except Exception as e:
        print(f"❌ Error validando el guion con Pydantic: {e}")
        return None


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


def _run_av_pipeline(script_dto: ScriptDTO, theme_config: ThemeConfig, video_path: str, topic: str):

    print("-> Generating audio and capturing durations...")
    script_dto = generate_script_audio_v2(script_dto, theme_config)

    total_duration = sum(seg.duration for seg in script_dto.segments)
    print(f"-> Total duration: {total_duration:.2f}s")

    temp_audio_path = "temp_dialogue.mp3"
    final_audio_path = assemble_dialogue_v2(script_dto, temp_audio_path)

    try:
        subtitle_gen = SubtitleGenerator(config)
        subtitle_clips = subtitle_gen.create_subtitle_clips_v2(script_dto)

        create_final_video(
            voice_path=final_audio_path,
            music_path=theme_config.music_path,
            video_background_path=video_path,
            output_path=str(get_project_root() / "output" / f"{topic.replace(' ', '_').lower()}.mp4"),
            duration_sec=round(total_duration),
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

        print("-> Validating Script with Pydantic DTO...")
        try:
            script_data = json.loads(script_json_str)
            script_dto = ScriptDTO(topic=request.topic, segments=script_data)
        except Exception as e:
            print(f"❌ Error al mapear el DTO: {e}")
            return

        _run_av_pipeline(script_dto, theme_config, video_path, request.topic)


# def _handle_story_series_flow(request: VideoRequest, theme_config: ThemeConfig, video_path: str):
#     """Handles the generation of multi-part story videos."""
#     json_series_str = generate_formatter_script_json(
#         time_limit=request.duration_seconds,
#         theme_config=theme_config,
#         context_story=request.context_story
#     )
#
#     try:
#         multi_part_scripts_data = json.loads(json_series_str)
#     except json.JSONDecodeError as e:
#         print(f"Fatal error: The JSON returned by Gemini is not valid. {e}")
#         return
#
#     if not multi_part_scripts_data:
#         print("ERROR: Multi-part story segmentation failed.")
#         return
#
#     # Iteramos sobre cada parte (Part 1, Part 2, etc.)
#     for part_data in multi_part_scripts_data:
#         part_number = part_data.get("part_number", 1)
#         script_lines = part_data.get('script_lines', [])
#
#         # --- MAPEO A DTO (Super_Edits) ---
#         try:
#             # Creamos un ScriptDTO para esta parte específica
#             script_dto = ScriptDTO(
#                 topic=f"{request.topic} - Part {part_number}",
#                 segments=script_lines
#             )
#
#             # Enviamos el DTO al pipeline
#             _run_av_pipeline(
#                 script_dto=script_dto,
#                 theme_config=theme_config,
#                 video_path=video_path,
#                 topic=request.topic,
#                 output_suffix=f"_part_{part_number}"  # Asegúrate que _run_av_pipeline acepte este kwarg
#             )
#         except Exception as e:
#             print(f"❌ Error validando la parte {part_number}: {e}")
#             continue


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

    try:
        script_data = json.loads(script_json_str)
        script_dto = ScriptDTO(
            topic=request.topic,
            segments=script_data
        )

        _run_av_pipeline(script_dto, theme_config, video_path, request.topic)

    except Exception as e:
        print(f"Critical Error when validating with Pydantic: {e}")
        print(f"Json Content failed: {script_json_str[:200]}...")
        return

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

# Example usage, this will be move to an API endpoint later

if __name__ == "__main__":

    _context_story = """This 5‑minute video would create a eerie unsettling and dwon right terrifying story about the shadow people as a creepypasta monologue.
    
    INSTRUCTIONS: 
    Narration should be slow and serious toned
    Should emphasise in the fact that the shadow people can be anywhere and its presence is unnatural.
    
    IMPORTANT: Use the following story as baseline but create a more terrifying version, this should leave the viewer thinking if the really saw something through the corner of their eye
    
    Those little flickers of darkness you see out of the corner of your eye? Those aren’t just spots, or dust, or a trick of light. Maybe they’re ghosts, as some people believe, but I’m convinced they’re the Shadow People – beings from a dimension close to our own, but not able to be seen when we focus fully on them.

    I have always been able to see the Shadow People. When I was young, my mother had my eyes checked by several different optometrists because I complained about the things I saw. I learned to keep quiet about them, but it took a while.
    
    My first encounter with them took place when I was three or four years old. We lived in a high rise flat with a sweeping view of the hills and the city below us. My best friend at the time, Michelle, was over on a playdate; her family lived across the landing and we spent more time together than apart. That day, she greeted me by running into my room, fueled by a ridiculous burst of enthusiasm.
    
    “We have to play with my new dolls!” she screeched at me. I was much more into dinosaurs and bugs, and that sounded like a terrible way to spend an afternoon.
    
    “No,” I insisted. “We have to play imagination! Godzilla vs. the killer wasps!” I tried to stomp around the room and look menacing.
    
    Michelle huffed and disappeared. She was much faster than I was, and I wasn’t very good at finding hiding people, but for all that, I should have seen her when I turned the corner — and I didn’t.
    
    Then I saw a shadow lurking at the corner of my vision. Thinking it must be Michelle, I turned towards it, calling her name. There was no answer, and the shadow continued to dance and dart out of range of my direct stare, as if it were avoiding making eye contact with me.
    
    As the years went by, I began to believe that the Shadow People were my friends, or even my protectors, like guardian angels. But then the nights became terrifying. I started to see the Shadow People in the real shadows of my room. Many of them darted away when I tried to stare at them, but others hung around in the corners, clustering like cobwebs.
    
    Then the noise started.
    
    It was like wind caressing leaves until they whispered. It was a language I couldn’t comprehend, words I knew I would never understand unless I was somehow in their dimension. As the whispering grew more frenetic, the Shadow People began to come together and move towards me.
    
    I bolted to my parents and shook them awake. Of course, they didn’t believe me, trying to coax me into believing it was just a dream or my imagination.
    
    I know it was the Shadow People. And if you see a shadow within the shadows, or a shape flitting at the edge of your vision, you may not be alone.
    
    """


    # Example using the VideoRequest Data Class
    video_request = VideoRequest(
        topic="The shadow people (creepypasta)",
        duration_seconds=100, # Approx time duration, need to work on accuracy
        theme="horror", # Which theme is your video like (redit stories, top 5, horror, etc, if not exists with will use default)
        use_template=True, # Template for monologue type
        is_monologue=True, # Use monologue features such as the new prompt refiner
        context_story=_context_story, # Your context
        # video_index=0  # Optional # To select a video, this will be useful for web application
    )

    create_short_from_json(video_request)
