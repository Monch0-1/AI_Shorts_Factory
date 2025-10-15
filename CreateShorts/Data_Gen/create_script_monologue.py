import os
from google import genai
from google.genai import types
from CreateShorts.theme_config import ThemeConfig
from CreateShorts.Create_Short_Service.loadEnvData import load_env_data


def generate_monolog_script_json(topic: str, time_limit: int, theme_config: ThemeConfig, context_story: str = None) -> str:
    # 1. Inicialización y Configuración
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')

    # Obtener la configuración de esquema e instrucción del tema cargado
    script_schema = theme_config.prompting.script_schema
    _system_instruction = theme_config.prompting.system_instruction

    # 2. Construcción del Prompt Principal
    # Usamos la historia de contexto si se proporciona, si no, usamos el topic.
    story_context = context_story if context_story else topic

    prompt_template = f"""
    You are a master script editor and adapter for short-form social media narratives. 

    **PRIMARY INSTRUCTION:** Generate a first-person monologue script. The entire script must be **in English** and follow the structured JSON format provided.

    **SOURCE MATERIAL:** Adapt the following high-level story concept into a compelling, short-form monologue.

    CONTEXT: {story_context} 

    DURATION: The total read time should aim for {time_limit} approximately within a range of plus 20%, considering this will be used for a TTS audio file so the duration could go higher than expected.

    **NARRATIVE STYLE & TONE:**
    1. The speaker is a 'Survivor' or 'Witness' will be defined as 'Anon', recounting a personal experience (first-person).
    2. The style must be focused on the narrative's core emotion (e.g., Dread, Vengeance, Amused Reflection).
    3. The narrative must flow line-by-line, maintaining a clear tone defined by the 'mood' field.

    **Json Format:** Use short lines of text; if a line is longer than 10 words, break it into multiple lines for short subtitles.
    **End**: The monologue must conclude with a strong, definitive final thought, an ambiguous or unsettling question, or funny comment given the context.

    Strictly adhere to the established character roles and return **ONLY** the JSON array structure.
    """

    # 3. Llamada a la API
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_template,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=script_schema,
                system_instruction=_system_instruction,
                temperature=0.7  # Una temperatura neutral, adecuada para historias
            )
        )
        # El texto de respuesta será una cadena JSON válida
        return response.text

    except Exception as e:
        return f"Error en la generación del guion JSON: {e}"