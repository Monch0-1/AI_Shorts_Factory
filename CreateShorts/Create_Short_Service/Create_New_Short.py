import os
from pathlib import Path

from CreateShorts.Data_Gen.create_audio import assemble_dialogue_pydub
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Data_Gen.mix_assets import create_final_video
from CreateShorts.Data_Gen.text_to_speach import generate_dialogue_audio
from create_video import get_absolute_path


def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    return Path(__file__).parent.parent

def create_complete_short(topic: str, duration_seconds: int):
    """
    Creates a complete short video from start to finish.
    """
    print(f"-> Starting short video creation for topic: {topic}")
    
    # 1. Generate the script
    print("-> Generating script...")
    script_json = generate_debate_script_json(topic, duration_seconds)
    
    # 2. Generate audio chunks in memory
    print("-> Converting script to audio...")
    audio_chunks = generate_dialogue_audio(script_json)
    
    if not audio_chunks:
        print("ERROR: Failed to generate audio chunks")
        return
    
    # 3. Assemble audio chunks
    print("-> Assembling audio chunks...")
    temp_audio_path = "temp_dialogue.mp3"
    final_audio_path = assemble_dialogue_pydub(audio_chunks, temp_audio_path)
    
    if not final_audio_path:
        print("ERROR: Failed to assemble audio")
        return
    
    # 4. Create the final video
    # Using project root to locate resources



    project_root = get_project_root()
    background_music = str(project_root / "resources" / "audio" / "2_23_AM.mp3")
    background_video = str(project_root / "resources" / "video" / "4.mp4")
    output_video_file = str(project_root / "output" / "final_short.mp4")

    os.makedirs(os.path.dirname(output_video_file), exist_ok=True)

    try:
        create_final_video(
            final_audio_path,
            background_music,
            background_video,
            output_video_file,
            duration_seconds,
        )
    finally:
        import time
        time.sleep(1)

        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except PermissionError:
                print(f"Temp file was not deleted: {temp_audio_path}")


if __name__ == "__main__":
    background_img = get_absolute_path(".venv/Scripts/background.jpg")
    output_video = get_absolute_path("final_short.mp4")
    
    create_complete_short(
        topic="All you need to know about Lauma in 60 seconds (Genshin Impact)",
        duration_seconds=60,
    )