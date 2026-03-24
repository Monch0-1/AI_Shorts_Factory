import json
import random
import os
import time
from pathlib import Path
from typing import Final, Optional, Union
from dataclasses import dataclass

from CreateShorts.Models.script_models import ScriptDTO
from CreateShorts.Models.video_models import VideoRequest, VideoOptions
from CreateShorts.Data_Gen.create_audio import assemble_dialogue_v2
from CreateShorts.Data_Gen.mix_assets import create_final_video
from CreateShorts.Data_Gen.text_to_speach import clean_temp_audio
from CreateShorts.Data_Gen.subtitle_generator import SubtitleGenerator, SubtitleConfig
from CreateShorts.Data_Gen.formatter_script import generate_formatter_script_json
from CreateShorts.Factory.factory import get_script_provider, get_audio_provider
from CreateShorts.theme_config import ThemeManager, ThemeConfig
from CreateShorts.utils import sanitize_filename, get_project_root

MAX_TIME_LIMIT: Final[int] = 120

# Future update Skyreels.ai
# Create custom configuration (optional)

try:
    import imageio_ffmpeg
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    print("✅ FFmpeg configured successfully")
except Exception as e:
    print(f"⚠️ FFmpeg configuration warning: {e}")

config = SubtitleConfig(
    fontsize=45,
    font='Arial-Bold',
    color='white',
    stroke_color='black',
    stroke_width=2
)


def parse_script_to_dto(topic: str, script_json_str: str) -> Optional[ScriptDTO]:
    try:
        data = json.loads(script_json_str)
        if isinstance(data, list):
            return ScriptDTO(topic=topic, segments=data)
        return ScriptDTO(**data)
    except Exception as e:
        print(f"❌ Error validating script with Pydantic: {e}")
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


def _run_av_pipeline(script_dto: ScriptDTO, theme_config: ThemeConfig, video_path: str, topic: str, include_sfx: bool = True):
    """
    Final assembly pipeline. 
    Receives a DTO that ALREADY has loaded audios and durations.
    """
    # 1. Calculate total duration (already comes in the DTO thanks to the audio service)
    total_duration = sum(seg.duration for seg in script_dto.segments)
    print(f"-> Total duration: {total_duration:.2f}s")

    # Usar ruta relativa más flexible para Docker
    project_root = get_project_root()
    temp_dir = project_root / "temp"
    temp_dir.mkdir(exist_ok=True)
    temp_audio_path = temp_dir / "temp_dialogue.mp3"

    final_audio_path = assemble_dialogue_v2(script_dto, theme_config, str(temp_audio_path), include_sfx=include_sfx)
    
    # Validación crítica antes de continuar
    if not final_audio_path:
        print("❌ CRITICAL ERROR: Audio assembly failed, cannot proceed with video creation")
        return
        
    if not os.path.exists(final_audio_path):
        print(f"❌ CRITICAL ERROR: Final audio file not found: {final_audio_path}")
        return

    try:
        # 3. Generate Subtitles
        subtitle_gen = SubtitleGenerator(config)
        subtitle_clips = subtitle_gen.create_subtitle_clips_v2(script_dto)

        # 4. Crear directorio de salida
        output_dir = get_project_root() / "output"
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / f"{sanitize_filename(topic)}.mp4"

        # 5. Final Rendering
        create_final_video(
            voice_path=final_audio_path,
            music_path=theme_config.music_path,
            video_background_path=video_path,
            output_path=str(output_path),
            duration_sec=round(total_duration),
            subtitle_clips=subtitle_clips,
            background_volume=theme_config.music_volume
        )
        
        print("✅ SUCCESS: Video creation pipeline completed successfully")
        
    except Exception as e:
        print(f"❌ ERROR in video creation pipeline: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup of temporary .mp3 files
        clean_temp_audio()


def _handle_story_series_flow(request: VideoRequest, theme_config: ThemeConfig, video_path: str):
    """Handles the generation of multi-part story videos."""
    json_series_str = generate_formatter_script_json(
        time_limit=request.options.duration_seconds,
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
            script_data = json.loads(single_script_json_str)  # Fixed variable name
            script_dto = ScriptDTO(topic=request.topic, segments=script_data)
        except Exception as e:
            print(f"❌ Error mapping the DTO: {e}")
            return

        _run_av_pipeline(script_dto, theme_config, video_path, request.topic, include_sfx=request.options.include_sfx)

def _handle_standard_flow(request: VideoRequest, theme_config: ThemeConfig, video_path: str):
    """Handles standard videos using injected services."""

    # 1. Get providers according to environment (.env)
    script_service = get_script_provider()
    audio_service = get_audio_provider()

    # 2. Generate the script (The service decides if it's Real or Mock internally)
    script_json_str = script_service.generate(
        topic=request.topic,
        time_limit=request.options.duration_seconds,
        theme_config=theme_config,
        context=request.context_story,
        use_template=request.options.use_script_template,
        is_monologue=request.is_monologue,
        enable_refiner=request.options.enable_refiner
    )

    print(script_json_str)

    # 3. DTO mapping and Pipeline
    script_dto = parse_script_to_dto(request.topic, script_json_str)
    if script_dto:
        # The audio_service will also detect if it's Mock or Real
        script_dto = audio_service.synthesize(script_dto, theme_config)
        _run_av_pipeline(script_dto, theme_config, video_path, request.topic, include_sfx=request.options.include_sfx)

def create_complete_short(topic: str, duration_seconds: int, theme: str = "default", use_script_template: bool = False,
                          is_monologue: bool = False, context_story: str = "", video_index: int = None,
                          enable_refiner: bool = False, include_sfx: bool = True):
    """
    Creates a complete short video from start to finish.
    
    Args:
        topic (str): Topic for the video content
        duration_seconds (int): Desired duration in seconds
        theme (str): Theme name to use for video configuration
        use_script_template (bool): Whether to use a script template
        context_story (str): Context story for the video
        video_index (int): Optional index to select a specific video
        is_monologue (bool): Whether this is a monologue
        enable_refiner (bool): Whether to use the prompt refiner
        include_sfx (bool): Whether to include SFX in the final video
    """

    options = VideoOptions(
        duration_seconds=duration_seconds,
        video_index=video_index,
        enable_refiner=enable_refiner,
        use_script_template=use_script_template,
        include_sfx=include_sfx
    )

    # Structure input data into a Request Object
    request = VideoRequest(
        topic=topic,
        theme=theme,
        is_monologue=is_monologue,
        context_story=context_story,
        options=options
    )

    print(f"-> Starting short video creation for topic: {request.topic}")
    print(f"-> Prompt Refiner: {'ENABLED' if request.options.enable_refiner else 'DISABLED'}")
    print(f"-> Using theme: {request.theme}")

    # Load theme config
    theme_manager = ThemeManager()
    theme_config = theme_manager.get_theme_config(request.theme)

    if theme_config is None:
        print(f"Error: Could not load theme configuration for '{request.theme}'")
        return

    print(f"-> Theme configuration loaded:")
    video_path = _select_video_resource(theme_config, request.options.video_index)
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
        duration_seconds=video_request.options.duration_seconds,
        theme=video_request.theme,
        use_script_template=video_request.options.use_script_template,
        is_monologue=video_request.is_monologue,
        context_story=video_request.context_story,
        video_index=video_request.options.video_index,
        enable_refiner=video_request.options.enable_refiner,
        include_sfx=video_request.options.include_sfx
    )

# Example usage, this will be moved to an API endpoint later
if __name__ == "__main__":
    start_time = time.time()

    _context_story = """
    BASE_TEXT:
    I've been working at myu current job for almost 10 years, I started as a part of the sales team and climb the ladder 
    to manager, recently the direction and management team decided that we need a new batch of interns to get fresh ideas
    this is not new, it happens about once a year when we hire interns and keep the most promising ones, so that was the same this year
    the new intern assigned for my team, Michael, started about a month before this events, he seemed a little bit to full of himself
    maybe over confidence in is decision, seems like he wanted to grab the spotlight and almost impose his ideas, I didn't 
    think much of it, people like that comes from time to time, but little by little things started to spyral out of control,
    I started to receive complains from my team, from some of the seniors even, seems like Michael was getting very friendly with the HR
    department, he was boasting about that and started pressure my team things like "if you don't agree maybe candice from HR 
    could hear about work place harassment", I called him to my office after some more offenses to have a serious conversation.
    "Michael, you cant threaten the staff just because dont agree with you or because they didn't bring coffee to you, if you
    keep this attitude I will have no other option but to let you go", for a week that was the end of it, but a few days after
    I got a meeting from HR, Michael was there crying, Candice, her bestie from HR was upset, "We take workplace harassment very
    seriously here Anon, do you think this is appropriated from a staff manager to say to an intern, what do you think our 
    reputation will end up", I checked the files Candice wasd referring to in the table, copies of fabricated email saying 
    just the worst things, things that wold get you out to the streets in no time, work abuse, inappropriate behaviour, physical
    violence threads, the whole package, I got off with a serious warning, I was not fired because I have a good reputation
    with my colleagues anh the direction team, but I was warned there is no second time, later that day I found Michael
    sitting in my office, when I arrived he just said, "You better know from now and on who makes decisions in this office,
    I could not get you fired this time but you heard, there will not be another chance, this works in my favor so you better
    behave", he smirk and got out, I saw his expression change from smug to victim before he got out the door, I have to face 
    this kid again but I dont even know what he did or how he did it, what should I do?
    
    INSTRUCTIONS:
    - Create a relatable story  from the given BASE_TEXT
    - The story should have a Hook, build up, conflict and cliffhanger
    - The story narrative format should aim to be a social media story telling
    - Should be formatted also as a viral capable content
    - Aim to have rage bait, viral and retention content
    - The main character is Anon
    """

    # Example using the new nested structure
    video_options = VideoOptions(
        duration_seconds=120,
        video_index=None,
        enable_refiner=False, 
        use_script_template=True,
        include_sfx=False
    )

    video_request = VideoRequest(
        topic="The new intern at my company is trying to get me fired",
        theme="reddit", # Which theme is your video like (redit stories, top 5, horror, etc, if not exists with will use default)
        is_monologue=True, # Use monologue features such as the new prompt refiner
        context_story=_context_story, # Your context
        options=video_options
    )

    create_short_from_json(video_request)

    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "="*60)
    print(f"⏱️  TOTAL EXECUTION TIME: {total_time:.2f} seconds")
    print(f"📅 FINISHED AT: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")