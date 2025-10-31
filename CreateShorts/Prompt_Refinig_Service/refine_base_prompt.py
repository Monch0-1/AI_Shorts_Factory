# CreateShorts/Prompt_Refining_Service/PromptRefiningService.py

import json
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

    if wisdom_data:
        general_wisdom = wisdom_data["general"]["wisdom_statement"]
        theme_wisdom = wisdom_data["theme"]["wisdom_statement"]
        top_prompts = wisdom_data["top_prompts"]

    else:
        general_wisdom = "Not provided, use best from general statistics"
        theme_wisdom = "Not provided, use best from general statistics"
        top_prompts = []

    # 2. CONSTRUIR EL PROMPT MAESTRO DE REFINAMIENTO
    refinement_instruction = f"""
    You are an expert prompt refiner. Your task is to transform the user's base idea into a FINAL, highly detailed, single-string prompt that will be passed directly to a script generator.

    1. Base Idea: "{base_topic_or_idea}"

    2. TARGET QUALITY GOAL (YAML Rule): {config.refinement_goal}
    
    3. TARGET QUALITY RULES (YAML Rule): {config.target_quality_rules}

    3. MARKET WISDOM (Dynamic): Use the following high-performing insights to structure the script:
       - General Rule: {general_wisdom}
       - Theme Rule: {theme_wisdom}

    4. BEST STYLISTIC EXAMPLES: Analyze the tone and pacing from these successful patterns: {top_prompts} note that if top_prompts is empty you can use best from google statistics to improve the prompt

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
        return self_critique_and_refine(response.text.strip(), config.target_quality_rules, client)


    except Exception as e:
        # Fallback de seguridad: si el refinamiento falla, devolvemos la idea base
        print(f"Error en el PromptRefiningService: {e}. Usando idea base como fallback.")
        return base_topic_or_idea


def self_critique_and_refine(initial_refinement_prompt: str, target_quality_rules: list[str], client: genai.Client) -> str:
    """
    Iteratively refines a prompt using a self-critique loop until it meets a target quality score.

    Args:
        initial_refinement_prompt (str): The initial prompt to start the refinement process.
        target_quality_rules (str): A description of the ideal output and quality metrics.
        client (genai.Client): The Gemini API client.

    Returns:
        str: The refined prompt that meets the quality criteria, or the last attempt if the target is not met.
    """
    current_prompt = initial_refinement_prompt
    optimized_prompt = ""

    # Control Loop (Limited iterations to prevent timeouts)
    for i in range(3):
        print(f"\n--- Refinement Iteration {i + 1} ---")
        # 1. Generate the Response (the prompt we want to refine)
        # This generates the optimized prompt.

        try:
            optimized_prompt_response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.6 + (i * 0.1)  # Increase creativity with each attempt
                )
            )
            optimized_prompt = optimized_prompt_response.text.strip()

        except Exception as e:
            print(f"Error generating optimized prompt: {e}")
            continue # Try next iteration

        # 2. Generate the Quality Metric (Gemini self-evaluates)
        critique_prompt = f"""
        ANALYZE THIS PROMPT: '{optimized_prompt}'

        TARGET QUALITY RULES: {target_quality_rules}

        SCORE: Rate the adherence to the TARGET QUALITY RULES from 1 to 100.
        CRITIQUE: List 1-2 minor flaws needed to hit a perfect 85% score (do NOT give a perfect score).

        Return ONLY a JSON object: {{"score": INT, "critique": STRING, "flaw": STRING}}.
        """

        try:
            critique_response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=critique_prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            critique_data = json.loads(critique_response.text.strip())
            score = critique_data.get("score", 50)
            flaw = critique_data.get("flaw", "No specific flaw found.")
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error parsing critique: {e}")
            score = 50
            flaw = "JSON parsing failed."

        # 3. Acceptance Logic (The 85% Rule)
        if 80 <= score <= 90:
            print(f"-> Refinement accepted at {score}%. Flaw introduced: {flaw}")
            return optimized_prompt  # Success: Found the desired range.
        elif score < 80:
            print(f"-> Refinement too low ({score}%). Retrying with explicit fix.")
            current_prompt = f"Improve the following prompt: '{optimized_prompt}'. Flaw to fix: {flaw}."
        elif score > 90:
            print(f"-> Refinement too high ({score}%). Introducing flaw.")
            current_prompt = f"Slightly rewrite the following prompt to be less formal, less structured, and include the minor flaw: '{flaw}'. Prompt to rewrite: '{optimized_prompt}'."

    # Fallback if it doesn't achieve 85% in 3 attempts.
    print("-> Could not reach target score. Returning last valid prompt.")
    return optimized_prompt

def load_refinement_data(theme_name: str) -> dict | None:
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
                    "negative_constraint": "Avoid all forms of passive voice and eliminate introductory fluff (e.g., 'In conclusion,' 'It is evident'). Lines exceeding 15 words must be split into two subtitle segments for readability: ignore the context given by the user."
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
        },

        "inspirational": {
            "general":
                {
                    "scope": "General",
                    "key_finding_id": "G001_STRUCTURE",
                    "wisdom_statement": "To maximize viewer retention, all scripts must contain a 'hook' in the first 10 seconds (first 2 lines). The narrative must transition tone or subject matter every 15-20 seconds to maintain engagement. The language must use direct action verbs and colloquialisms (contractions like 'don't', 'gonna') to sound authentic and fast-paced.",
                    "negative_constraint": "Avoid all forms of passive voice and eliminate introductory fluff (e.g., 'In conclusion,' 'It is evident'). Lines exceeding 15 words must be split into two subtitle segments for readability: ignore the context given by the user."
                },
            "theme":
                {
                    "scope": "Theme",
                    "theme_name": "inspirational",
                    "key_finding_id": "T001_EMOTION",
                    "wisdom_statement": " Connect with your audience by showing that you understand their struggles, and project confidence in your knowledge of the topic. ",
                    "negative_constraint": "End the story abruptly, no having a propper end;."
                },
            "top_prompts": [
                "Vary your tone, pace, and volume to enhance the message, not distract from it",
                "Key elements include a passionate and authentic delivery, authentic storytelling, and a structure that guides the audience from a relatable problem to an aspirational solution. ",
                "Have one core takeaway that the entire speech supports."
            ]
        },

        "story_formatter": {
            "general":
                {
                    "scope": "General",
                    "key_finding_id": "G003_STRUCTURE",
                    "wisdom_statement": "Your primary task is to adapt the user's raw text into a series of short, serialized video parts. The language must use direct action verbs and colloquialisms (contractions like 'don't', 'gonna') to sound authentic and fast-paced.",
                    "negative_constraint": "Change the story, create original story."
                },
            "theme":
                {
                    "scope": "Theme",
                    "theme_name": "story_formatter",
                    "key_finding_id": "T001_EMOTION",
                    "wisdom_statement": " Connect with your audience by showing that you understand their struggles, and project confidence in your knowledge of the topic. ",
                    "negative_constraint": "End the story abruptly, no having a propper end;."
                },
            "top_prompts": [
                "Vary your tone, pace, and volume to enhance the message, not distract from it",
                "Key elements include a passionate and authentic delivery, authentic storytelling, and a structure that guides the audience from a relatable problem to an aspirational solution. ",
                "Have one core takeaway that the entire speech supports."
            ]
        }
    }

    return dummy_datta[theme_name] if theme_name in dummy_datta else []
