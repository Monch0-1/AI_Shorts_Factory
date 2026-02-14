import os
import tempfile
from typing import List
# from CreateShorts.Data_Gen.text_to_speach import AudioChunkInfo

from moviepy.editor import AudioFileClip, concatenate_audioclips, CompositeAudioClip
from CreateShorts.Create_Short_Service.Models.script_models import ScriptDTO
from CreateShorts.theme_config import ThemeConfig


# def assemble_dialogue_pydub(audio_chunks: List[AudioChunkInfo], output_filename: str):
#     global temp_dir
#     audio_clips = []
#     temp_files = []
#
#     try:
#         temp_dir = tempfile.mkdtemp()
#
#         for i, chunk_info in enumerate(audio_chunks):
#             temp_path = os.path.join(temp_dir, f'temp_chunk_{i}.mp3')
#             with open(temp_path, 'wb') as f:
#                 f.write(chunk_info.content)
#             temp_files.append(temp_path)
#
#             audio_clip = AudioFileClip(temp_path)
#             audio_clips.append(audio_clip)
#
#         if audio_clips:
#             final_audio = concatenate_audioclips(audio_clips)
#             final_audio.write_audiofile(output_filename)
#             print(f"-> Audio assembly finished: {output_filename}")
#
#     finally:
#         # Clean up clips and temporary files
#         for clip in audio_clips:
#             clip.close()
#
#         for temp_file in temp_files:
#             if os.path.exists(temp_file):
#                 os.remove(temp_file)
#
#         if os.path.exists(temp_dir):
#             os.rmdir(temp_dir)
#
#     return output_filename


def assemble_dialogue_v2(script_dto: ScriptDTO, theme_config: ThemeConfig, output_filename: str):

    voice_clips = []
    sfx_clips = []
    current_time = 0.0

    print(f"-> Starting Advanced Audio Assembly for topic: {script_dto.topic}")

    try:
        for segment in script_dto.segments:
            if not segment.audio_path or not os.path.exists(segment.audio_path):
                continue

            v_clip = AudioFileClip(segment.audio_path).set_start(current_time)
            voice_clips.append(v_clip)

            # 2. Lógica de Highlights (SFX)
            if segment.highlight:
                h_type = segment.highlight.type  # ej: "funny"
                h_context = segment.highlight.context  # ej: "counter"

                resources = getattr(theme_config, 'resources', {})
                options = resources.get(h_type, {}).get(h_context, [])

                if options:
                    selected_sfx = random.choice(options)
                    sfx_path = selected_sfx.get('path')

                    if sfx_path and os.path.exists(sfx_path):
                        print(f"   [Highlight] Inserting {selected_sfx['name']} at {current_time:.2f}s")

                        sfx_clip = AudioFileClip(sfx_path).set_start(current_time)

                        sfx_clip = sfx_clip.volumex(0.8)
                        sfx_clips.append(sfx_clip)

            current_time += segment.duration

        final_composition = CompositeAudioClip(voice_clips + sfx_clips)

        print(f"-> Exporting Master Audio with {len(sfx_clips)} effects...")
        final_composition.write_audiofile(output_filename, fps=44100, logger=None)

        return output_filename

    except Exception as e:
        print(f"❌ ERROR in Highlight Mixer: {e}")
        return None
    finally:
        # Limpieza de memoria (Crucial en Windows)
        for clip in voice_clips + sfx_clips:
            clip.close()