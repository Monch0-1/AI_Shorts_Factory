import os
from typing import Final

from google import genai
from google.genai import types
from CreateShorts.theme_config import ThemeConfig
from CreateShorts.Create_Short_Service.loadEnvData import load_env_data

WORDS_PER_MINUTE: Final[int] = 250
SECONDS: Final[int] = 60

def generate_formatter_script_json(time_limit: int, theme_config: ThemeConfig, context_story: str) -> str:
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')

    script_schema = theme_config.prompting.script_schema
    _system_instruction = theme_config.prompting.system_instruction

    prompt_template = f"""
    **SYSTEM INSTRUCTION:** {_system_instruction}

    **PRIMARY TASK: MULTI-PART STORY SEGMENTATION**

    Your primary task is to adapt the user's raw text into a series of short, serialized video parts.

    **TARGET DURATION PER PART:** The total read time per part should aim for {int(time_limit * WORDS_PER_MINUTE / SECONDS)} words for the time limit given approximately withing range of plus 20%, consider this will be used for a TTS audio file so the duration could go higher than expected.
    
    **RULE FOR FINAL SEGMENT MERGING (STRICT):** If, after dividing the story, the final segment (Part N) has an estimated duration of **less than 100 seconds**, you **MUST** merge the content of that final segment into the preceding segment (Part N-1). 
    The goal is to prevent any segment, except for a full story under 150 seconds, from being less than 100 seconds long.

    **RULES FOR DIVISION (CRITICAL DO NOT IGNORE):**
    1.  **LOGICAL CUTS:** Do NOT cut in the middle of a sentence or a thematic idea. The division point between parts must be a natural narrative break (a change of location, a new character introduction, or a major decision point).
    2.  **CLIFFHANGER ENDING:** The final 5 seconds of every part (except the last one) MUST create a moment of tension or unanswered curiosity to encourage the viewer to watch the next part (a subtle cliffhanger) here and only here you can add the phrase -This is the end of the video, follow for more- as a casual farewell.
    3.  **NO CONTENT MODIFICATION:** Do not add commentary, change the core meaning, or introduce new opinions to the original story, do not modify the original text.
    4.  **Json Format:** If a dialog is longer than 20 words, break it into multiple lines from the same narrator to keep consistency, 
                      the line dialog overall can be over 20 words, we are breaking it just to have short subtitles NOT TO HAVE SHORT DIALOGS(this for short subtitles).
    5. **TITLE FOR EACH PART:** Each part must start with the title name if there is more than 1 part then the phrase Part N must be added, where N represents the number of the part being created

    SOURCE TEXT TO SEGMENT:
    ---
    {context_story}
    ---

    **FINAL OUTPUT:** Apply the segmentation and use the provided Multi-Part JSON Schema. Generate all necessary parts to tell the complete story.

    Return **ONLY** the JSON array structure.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_template,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=script_schema,
                system_instruction=_system_instruction,
                temperature=0.7
            )
        )
        return response.text

    except Exception as e:
        return f"Error in JSON script generation: {e}"