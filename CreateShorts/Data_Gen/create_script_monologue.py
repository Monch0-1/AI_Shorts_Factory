import json
from typing import Final

from google import genai
from google.genai import types
from CreateShorts.theme_config import ThemeConfig, ThemeManager
from CreateShorts.loadEnvData import load_env_data
from CreateShorts.config import WORDS_PER_MINUTE, SECONDS_PER_MINUTE as SECONDS

def generate_monolog_script_json(
        final_script_prompt: str,
        time_limit: int,
        theme_config: ThemeConfig,
        context: str = None
) -> str:
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')
    theme_manager = ThemeManager()

    script_schema = theme_config.prompting.script_schema
    _system_instruction = theme_config.prompting.system_instruction
    speaker = "Narrator_Male"
    sfx_mapping = theme_manager.get_sfx_mapping()

    # 1. FINAL PROMPT CONSTRUCTION
    # The refined prompt already includes the story, style and guidelines.
    # We only add the final formatting and length instructions.

    prompt_template = f"""
        You are a master script editor and adapter for short-form social media narratives.

        **PRIMARY INSTRUCTION (From Prompt Refiner):** {final_script_prompt}

        **DURATION:** The total read time should aim for a minimum of {time_limit} seconds and can go as long as needed, consider this will be used for a TTS audio file so the duration could go higher than expected.

        **FINAL FORMAT:** Adhere strictly to the JSON schema provided.
        
        **CONTEXT:** {context}
        
        **SPEAKER:** {speaker}
        
        **STYLE REQUIREMENTS:**
                1.  **Language:** ENTIRELY IN ENGLISH.
                2.  **Json Format:** If a dialog is longer than 20 words, break it into multiple lines from the same narrator to keep consistency, 
                      the line dialog overall can be over 20 words, we are breaking it just to have short subtitles NOT TO HAVE SHORT DIALOGS(this for short subtitles).
                3.  **End**: Finish with a nice casual farewell
                4.  **EDITION HIGHLIGHTS:** Identify key moments and tag them with an SFX highlight.
                   - 'category' MUST be one of: {list(sfx_mapping.keys())}
                   - 'desired_traits' MUST be a list of 2 to 5 descriptive strings for the sound's
                     texture and mood. Draw from or be inspired by this trait catalog:
                     {json.dumps(sfx_mapping, indent=4)}
                   - 'beat_delay' controls the pause after the SFX plays:
                     'none' = no pause, 'short' = 0.3s, 'long' = 0.7s (use for dramatic effect)

        Use the context given by the user to guide the script.

        Return **ONLY** the JSON array structure.
        """

    # 2. API call.
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