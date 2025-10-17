# CreateShorts/Prompt_Refining_Service/PromptRefiningService.py

from google import genai
from google.genai import types
from CreateShorts.theme_config import ThemeConfig
# Suponemos que tienes una función para cargar los datos de la Base de Conocimiento
# En producción, esto llamaría a MongoDB.

from ..Create_Short_Service.loadEnvData import load_env_data


def refine_base_prompt(base_topic_or_idea: str, theme_config: ThemeConfig) -> str:
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')
    config = theme_config.prompting

    # 1. OBTENER LA SABIDURÍA (Base de Conocimiento)
    # Carga la información de rendimiento (Dummy en esta etapa)
    wisdom_data = load_refinement_data(theme_config.name)

    general_wisdom = wisdom_data["general"]["wisdom_statement"]
    theme_wisdom = wisdom_data["theme"]["wisdom_statement"]
    top_prompts = wisdom_data["top_prompts"]

    # 2. CONSTRUIR EL PROMPT MAESTRO DE REFINAMIENTO
    refinement_instruction = f"""
    You are an expert prompt refiner. Your task is to transform the user's base idea into a FINAL, highly detailed, single-string prompt that will be passed directly to a script generator.

    1. Base Idea: "{base_topic_or_idea}"

    2. TARGET QUALITY GOAL (YAML Rule): {config.refinement_goal}

    3. MARKET WISDOM (Dynamic): Use the following high-performing insights to structure the script:
       - General Rule: {general_wisdom}
       - Theme Rule: {theme_wisdom}

    4. BEST STYLISTIC EXAMPLES: Analyze the tone and pacing from these successful patterns: {top_prompts}

    Output ONLY the finalized, single, highly-detailed prompt text, ready for script generation. Do NOT include any commentary.
    """

    # 3. LLAMADA A GEMINI PRO
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',  # Usamos PRO para la tarea de razonamiento
            contents=refinement_instruction,
            config=types.GenerateContentConfig(
                temperature=0.3  # Baja temperatura para precisión en el output del prompt
            )
        )
        return response.text.strip()

    except Exception as e:
        # Fallback de seguridad: si el refinamiento falla, devolvemos la idea base
        print(f"Error en el PromptRefiningService: {e}. Usando idea base como fallback.")
        return base_topic_or_idea

def load_refinement_data(theme_name: str) -> dict:
    """
    Carga los datos de refinamiento para un tema específico.
    
    Args:
        theme_name (str): Nombre del tema
        
    Returns:
        dict: Diccionario con la configuración de refinamiento que incluye:
            - general: Configuración general
            - theme: Configuración específica del tema
            - top_prompts: Lista de los mejores ejemplos (actualmente no implementado)
    """
    dummy_datta = {
        "reddit":{
            "general":
                {
                    "scope": "General",
                    "key_finding_id": "G001_STRUCTURE",
                    "wisdom_statement": "To maximize viewer retention, all scripts must contain a 'hook' in the first 10 seconds (first 2 lines). The narrative must transition tone or subject matter every 15-20 seconds to maintain engagement. The language must use direct action verbs and colloquialisms (contractions like 'don't', 'gonna') to sound authentic and fast-paced.",
                    "negative_constraint": "Avoid all forms of passive voice and eliminate introductory fluff (e.g., 'In conclusion,' 'It is evident'). Lines exceeding 15 words must be split into two subtitle segments for readability."
                },
            "theme":
                {
                    "scope": "Theme",
                    "theme_name": "reddit",
                    "key_finding_id": "T002_EMOTION",
                    "wisdom_statement": "For anecdotal content, the script must explicitly build empathy: use 'I was just trying to' or 'I didn't think it would happen' in the first two lines. The mood must sharply transition from 'Calm' or 'Amused' to 'Shocked' or 'Panic' in the final 30% of the script to create an effective emotional spike. The end should be witty, funny or insightful depending of the mood of the story.",
                    "negative_constraint": "Absolutely forbid to end the story abruptly a propper end is a must; the core action must be communicated rapidly."
                },
            "top_prompts": [
                              "The opening line immediately establishes a sense of quiet dread, and the monologue structure uses a consistent 'I saw / I felt' pattern.",
                              "The script successfully uses the 'Amused' mood to introduce the main conflict, transitioning abruptly to 'Shocked' in the middle and ending with 'Thoughtful'.",
                              "The pacing is exceptionally fast, averaging 1.1x speed, and the language relies heavily on contemporary internet slang and contractions to maintain authenticity."
                            ]
        }
    }

    return dummy_datta[theme_name] if theme_name in dummy_datta else []
