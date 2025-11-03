from moviepy.editor import AudioFileClip, concatenate_audioclips
import os
import tempfile
from typing import List
from CreateShorts.Data_Gen.text_to_speach import AudioChunkInfo

def assemble_dialogue_pydub(audio_chunks: List[AudioChunkInfo], output_filename: str):
    global temp_dir
    audio_clips = []
    temp_files = []
    
    try:
        temp_dir = tempfile.mkdtemp()
        
        for i, chunk_info in enumerate(audio_chunks):
            temp_path = os.path.join(temp_dir, f'temp_chunk_{i}.mp3')
            with open(temp_path, 'wb') as f:
                f.write(chunk_info.content)
            temp_files.append(temp_path)

            audio_clip = AudioFileClip(temp_path)
            audio_clips.append(audio_clip)

        if audio_clips:
            final_audio = concatenate_audioclips(audio_clips)
            final_audio.write_audiofile(output_filename)
            print(f"-> Audio assembly finished: {output_filename}")
            
    finally:
        # Clean up clips and temporary files
        for clip in audio_clips:
            clip.close()
        
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
    
    return output_filename