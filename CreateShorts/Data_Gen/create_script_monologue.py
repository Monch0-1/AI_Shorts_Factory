import os
from typing import Final

from google import genai
from google.genai import types
from CreateShorts.theme_config import ThemeConfig
from CreateShorts.Create_Short_Service.loadEnvData import load_env_data

WORDS_PER_MINUTE: Final[int] = 130
SECONDS: Final[int] = 60

def generate_monolog_script_json(
        final_script_prompt: str,
        time_limit: int,
        theme_config: ThemeConfig,
        context: str = None
) -> str:
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')

    script_schema = theme_config.prompting.script_schema
    _system_instruction = theme_config.prompting.system_instruction

    # 1. FINAL PROMPT CONSTRUCTION
    # The refined prompt already includes the story, style and guidelines.
    # We only add the final formatting and length instructions.

    prompt_template = f"""
        You are a master script editor and adapter for short-form social media narratives.

        **PRIMARY INSTRUCTION (From Prompt Refiner):** {final_script_prompt}

        **LENGTH RESTRICTION (CRITICAL):** The final script MUST contain **Approximately {int(time_limit * WORDS_PER_MINUTE / SECONDS)} WORDS** in total (range +/20%).

        **FINAL FORMAT:** Adhere strictly to the JSON schema provided.
        
        **CONTEXT:** {context}

        If a sentence is too long, you **MUST** break it into multiple separate lines/entries in the JSON array but keep natural conversation flow.
        **SUBTITLE READABILITY RULE (STRICT):** Each line in the JSON array must be short for optimized subtitles, natural phrase optimized for fast reading. 
        Lines **MUST NOT EXCEED 15 WORDS** without loosing propper narrative flow.

        Return **ONLY** the JSON array structure.
        """

    # 2. API call
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
        return f"Error en la generación del guion JSON: {e}"