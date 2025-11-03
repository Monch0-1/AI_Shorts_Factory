import os
from typing import Final

from google import genai
from google.genai import types
from CreateShorts.theme_config import ThemeConfig
from CreateShorts.Create_Short_Service.loadEnvData import load_env_data

WORDS_PER_MINUTE: Final[int] = 130
SECONDS: Final[int] = 60

def generate_formatter_script_json(time_limit: int, theme_config: ThemeConfig, context_story: str) -> str:
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')

    script_schema = theme_config.prompting.script_schema
    _system_instruction = theme_config.prompting.system_instruction

    prompt_template = f"""
    **SYSTEM INSTRUCTION:** {_system_instruction}

    **PRIMARY TASK: MULTI-PART STORY SEGMENTATION**

    Your primary task is to adapt the user's raw text into a series of short, serialized video parts.

    **TARGET DURATION PER PART:** Each individual part must result in a video of **approximately 60-75 seconds** in length. Use the word count estimation (approx. {int(75 * WORDS_PER_MINUTE / SECONDS)} words) to determine the cut points.
    
    **RULE FOR FINAL SEGMENT MERGING (STRICT):** If, after dividing the story, the final segment (Part N) has an estimated duration of **less than 60 seconds**, you **MUST** merge the content of that final segment into the preceding segment (Part N-1). 
    The goal is to prevent any segment, except for a full story under 75 seconds, from being less than 60 seconds long.

    **RULES FOR DIVISION (CRITICAL):**
    1.  **LOGICAL CUTS:** Do NOT cut in the middle of a sentence or a thematic idea. The division point between parts must be a natural narrative break (a change of location, a new character introduction, or a major decision point).
    2.  **CLIFFHANGER ENDING:** The final 5 seconds of every part (except the last one) MUST create a moment of tension or unanswered curiosity to encourage the viewer to watch the next part (a subtle cliffhanger).
    3.  **NO CONTENT MODIFICATION:** Do not add commentary, change the core meaning, or introduce new opinions to the original story.
    4.  **LINE MAX:** Each 'line' entry in the 'script_lines' array MUST be optimized for short subtitles and **MUST NOT EXCEED 10 WORDS**.

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