import os
from google import genai
from google.genai import types
from CreateShorts.theme_config import ThemeConfig
from CreateShorts.Create_Short_Service.loadEnvData import load_env_data

def generate_debate_script_json(topic: str, time_limit: int, theme_config: ThemeConfig, use_template: bool = False):
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')

    # Obtener la configuración correctamente del theme_config
    script_schema = theme_config.prompting.script_schema
    _system_instruction = theme_config.prompting.system_instruction

    if not use_template:
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
    else:
        prompt_template = f"""
                You are a highly skilled scriptwriter for short-form social media comedy, specializing in creating structured Top 5 lists and debates.
    
                **PRIMARY INSTRUCTION:** Generate a dialogue script about a "Top 5 List" between two distinct personalities, Nina and Tina. The entire script must be **in English** and follow the structured JSON format provided.
    
                **TOPIC:** The Top 5 {topic}.
    
                **STRUCTURED DEBATE FLOW:**
                The script MUST follow a structure where the list is presented, and Nina challenges the ranking/inclusion of at least 3 items.
                1.  **OPENING:** Casual greeting/topic setup. (1-2 lines)
                2.  **ITEMS 5, 4, 3:** Tina presents the item, Nina asks a skeptical/confused question about the item (e.g., "But isn't that too slow?"), and Tina defends the item with an analogy.
                3.  **ITEMS 2, 1:** Tina presents the final items, Nina expresses strong disagreement or surprise, and Tina delivers the final, witty defense.
                4.  **CLOSING:** Nina acknowledges the list, and Tina delivers a casual farewell. (1-2 lines)
    
                **DURATION:** The total read time should aim for {time_limit} aproximatedly withing range of plus 20%.
    
                **CHARACTERS & TONE:**
                * **Nina (The Skeptical Challenger):** Asks critical questions about the ranking or the drawbacks of an item. Must use contractions (e.g., "don't," "isn't that").
                * **Tina (The Witty Expert & Defender):** Explains the pros of the item using clear, often humorous analogies.
    
                **STYLE REQUIREMENTS:**
                1.  **Language:** ENTIRELY IN ENGLISH.
                2.  **Content:** Include at least one **humorous or simple analogy** from Tina per challenged item.
                3.  **Json Format:** Use short lines of text.
    
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
        # El texto de respuesta será una cadena JSON válida
        return response.text

    except Exception as e:
        return f"Error en la generación del guion JSON: {e}"