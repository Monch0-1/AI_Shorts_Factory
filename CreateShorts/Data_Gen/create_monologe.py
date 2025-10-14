import os
from google import genai
from google.genai import types

from CreateShorts.Create_Short_Service.loadEnvData import load_env_data


def generate_monologue_script(theme_topic: str, time_limit: int, theme_context_story: str = None):
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')

    # Esquema general (funciona para monólogo y diálogo)
    horror_monolog_schema = types.Schema(
        type=types.Type.ARRAY,
        description="List of lines in the first-person horror monologue.",
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "speaker": types.Schema(type=types.Type.STRING,
                                        # Siempre será 'Survivor' o 'Narrator'
                                        description="The single character speaking."),
                "line": types.Schema(type=types.Type.STRING,
                                     description="The concise line text of the monologue."),
                "mood": types.Schema(type=types.Type.STRING,
                                     # Esto es útil para el tono de voz si usas una API avanzada
                                     description="The emotional state of the speaker (e.g., Whispering, Panic, Dread, Resignation).")
            },
            # Solo requerimos el speaker (constante) y la línea.
            required=["speaker", "line", "mood"]
        )
    )

    _system_instruction = ""
    prompt_template = ""

    _system_instruction = (
        "You are a master scriptwriter for short, psychological horror monologues designed for social media. "
        "Your primary goal is to create a chilling, unsettling story told from a first-person perspective. "
        "The narrative should focus on dread, mystery, and a growing sense of unease, avoiding explicit gore but implying disturbing events or entities. "
        "The speaker is a 'Survivor' recounting their experience. Return ONLY a valid JSON array."
    )

    prompt_template = f"""
       Generate a first-person monologue script for a short horror video. The story should be genuinely unsettling and focus on psychological dread, not jump scares or gore.

       **SOURCE MATERIAL:** Use the following high-level story concept provided by the user. Your task is to adapt this concept into a short-form monologue.

       CONTEXT: {theme_context_story if theme_context_story else theme_topic} 

       DURATION: The total read time should aim for {time_limit} approximately within a range of plus 20%.

       STYLE REQUIREMENTS:
       1. The entire script must be in **ENGLISH**.
       2. The speaker is a 'Survivor' recounting a personal, terrifying experience.
       3. Build a sense of tension and mystery, leading to a chilling, ambiguous conclusion.
       4. Focus on sensory details (sounds, feelings, unsettling visuals implied) that contribute to the dread.

       **Json Format:** Use short lines of text, if a line is longer than 20 words, break it into multiple lines for short subtitles.
       **End**: The monologue should end on a note of lingering fear or an unsettling unanswered question.

       Strictly adhere to the established character roles and return ONLY the JSON array structure.
       """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_template,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=horror_monolog_schema,
                system_instruction=_system_instruction,
                temperature=0.7  # O puedes ajustar la temperatura para más intensidad en horror
            )
        )
        return response.text

    except Exception as e:
        return f"Error en la generación del guion JSON: {e}"


# --- Ejemplo de cómo llamarías a la función ---
# if __name__ == "__main__":
#     # Para un diálogo:
#     # dialogue_script = generate_script_json("AI vs Human Creativity", 45, script_type="dialogue")
#     # print("\n--- DIÁLOGO GENERADO ---")
#     # print(dialogue_script)
#
#     # Para un monólogo de terror:
#     topic = "The unsettling discovery of a house filled with objects that feel inexplicably wrong."
#
#     context_story = """
#     The story is about extreme isolation and psychological horror. A solitary man, deeply obsessed with his recently deceased mother, lives in a decaying farmhouse. Following his mother's death, he sealed her room off, leaving the rest of the house to rot. The core horror is that the man didn't just leave the house; he started filling it with objects made from things he found—things that looked like furniture, clothing, or bowls, but were clearly fabricated from human remains. The discovery of these household items is the central horrifying event. Focus on the sensory details of the house: the dust, the silence, the smell of decay, and the chilling realization that ordinary objects have been twisted into something macabre. The climax should be the discovery of a 'trophy' item made of human skin that suggests a deeper, terrifying obsession with identity.
#     """
#
#     horror_topic = "The unsettling silence of a remote cabin, where things keep moving when you're not looking."
#     horror_script = generate_monologue(topic, 60, context_story)
#     print("\n--- MONÓLOGO DE TERROR GENERADO ---")
#     print(horror_script)