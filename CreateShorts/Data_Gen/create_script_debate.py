import os
from google import genai
from google.genai import types

from CreateShorts.Create_Short_Service.loadEnvData import load_env_data

def generate_debate_script_json(topic: str, time_limit: int):
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')

    # 1. Definicion del esquema de salida (JSON)
    script_schema = types.Schema(
        type=types.Type.ARRAY,
        description="List of turns in the dialogue.",
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "speaker": types.Schema(type=types.Type.STRING, description="Nina or Tina"),
                "line": types.Schema(type=types.Type.STRING, description="The concise line text."),
                "topic": types.Schema(type=types.Type.STRING, description="The discussed subtopic.")
            },
            required=["speaker", "line", "topic"]
        )
    )

    # 1. Definición de las Reglas de Rol (System Instruction)
    _system_instruction = (
        "You are a highly skilled scriptwriter for short-form social media comedy and tech debates. "
        "Your primary goal is to write a casual, witty, and engaging dialogue strictly between two characters. "
        "Nina must pose skeptical, common-sense questions to expose flaws. "
        "Tina must provide clear, witty, and often funny analogies to explain complex concepts simply. "
        "The conversation must flow naturally without lecturing the audience. Return ONLY a valid JSON array."
    )

    prompt_template = f"""
        Based on the following topic, generate a dialogue script for two distinct personalities, Narrator A and Narrator B. 

        TOPIC: {topic}

        DURATION: The total read time should aim for {time_limit} aproximatedly withing range of plus 20%, consider this will be used for a TTS audio file so the duration could go higher than expected.

        STYLE REQUIREMENTS:
        1. The entire script must be in **ENGLISH**.
        2. Ensure Narrator A challenges Narrator B directly.
        3. Include at least one **humorous or simple analogy** from Narrator B.
        
        **CHARACTERS & TONE:**
        * **Nina (The Skeptical Beginner):** Speaks casually, uses contractions (e.g., "gonna," "don't"), and asks simple, common-sense questions to expose flaws or complexities. Must sound slightly frustrated or confused.
        * **Tina (The Witty Expert):** Speaks clearly, uses humor, and provides simple, fun analogies to explain complex solutions. Must have a friendly, lighthearted tone.
        * **Dialogue Style:** The conversation must flow naturally between A and B, maintaining a **casual, witty, and slightly exaggerated tone**. They are talking to each other, not lecturing the audience.
        
        **Content:** Include at least one **witty analogy** or **humorous example** from Narrator B.
        **Json Format:** Use short lines of text, if a dialog is longer than 20 words, break it into multiple lines (this for short subtitles).
        **End**: Finish with a nice casual farewell
    
        Strictly adhere to the established character roles and return ONLY the JSON array structure.
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
        # El texto de respuesta será una cadena JSON válida
        return response.text

    except Exception as e:
        return f"Error en la generación del guion JSON: {e}"