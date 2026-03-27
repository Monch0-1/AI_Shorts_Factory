import json
from typing import Final
from pathlib import Path
from google import genai
from google.genai import types
from CreateShorts.theme_config import ThemeConfig, ThemeManager
from CreateShorts.loadEnvData import load_env_data
from CreateShorts.ContextualDataService.ContextualDataGenerator import get_fresh_context

from CreateShorts.config import WORDS_PER_MINUTE, SECONDS_PER_MINUTE as SECONDS

def generate_debate_script_json(
        topic: str,
        time_limit: int,
        theme_config: ThemeConfig,
        use_template: bool = False,
        context: str = None
):
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')
    theme_manager = ThemeManager()

    # Get the configuration correctly from theme_config
    script_schema = theme_config.prompting.script_schema
    _system_instruction = theme_config.prompting.system_instruction
    sfx_mapping = theme_manager.get_sfx_mapping()

    if not use_template:
        context_generated = get_fresh_context(topic)
        prompt_template = f"""
            Based on the following topic, generate a dialogue script for two distinct personalities, Narrator A and Narrator B. 
    
            TOPIC: {topic}
            CONTEXT: {context_generated}
    
            DURATION: The total read time should aim for at least {int(time_limit * WORDS_PER_MINUTE / SECONDS)} words for the time limit given aproximatedly withing range of plus 20%, consider this will be used for a TTS audio file so the duration could go higher than expected.
    
            **CHARACTERS & TONE:**
            * **Nina (The Skeptical Beginner):** Speaks casually, uses contractions (e.g., "gonna," "don't"), and asks simple, common-sense questions to expose flaws or complexities. Must sound slightly frustrated or confused.
            * **Tina (The Witty Expert):** Speaks clearly, uses humor, and provides simple, fun analogies to explain complex solutions. Must have a friendly, lighthearted tone.
            * **Dialogue Style:** The conversation must flow naturally between A and B, maintaining a **casual, witty, and slightly exaggerated tone**. They are talking to each other, not lecturing the audience.
            
            **STYLE REQUIREMENTS:**
                1.  **Language:** ENTIRELY IN ENGLISH.
                2.  **Content:** Include at least one **humorous or simple analogy** from Tina.
                3.  **Json Format:** If a dialog is longer than 20 words, break it into multiple lines from the same narrator to keep consitency, the line dialog overall can be over 20 words, we are breaking it just to have short subtitles NOT TO HAVE SHORT DIALOGS(this for short subtitles).
                4. **End**: Finish with a nice casual farewell
                5. **EDITION HIGHLIGHTS:** Identify key moments and tag them with an SFX highlight.
                   - CRITICAL: You may use UP TO {max(1, time_limit // 20)} highlights total — use fewer or none if the
                     script does not have enough genuinely impactful moments. Never place two highlights
                     within 15 seconds of each other.
                   - 'category' MUST be one of: {list(sfx_mapping.keys())}
                   - 'desired_traits' MUST be a list of 2 to 5 descriptive strings for the sound's
                     texture and mood. Draw from or be inspired by this trait catalog:
                     {json.dumps(sfx_mapping, indent=4)}
                   - 'description' MUST be a single natural language sentence describing the exact sound
                     you want (e.g., "a quick cartoon bonk with a spring reverb tail"). This is used
                     as the generation prompt for ElevenLabs when no local asset matches.
                   - 'beat_delay' controls the pause after the SFX plays:
                     'none' = no pause, 'short' = 0.3s, 'long' = 0.7s (use for dramatic effect)
                   - 'placement': 'start' triggers the SFX at the beginning of the segment, 'end' triggers at the end
                   - 'offset_seconds': fine-tune trigger time in seconds (e.g. -0.2 to trigger slightly before)
                   - 'volume_modifier': dB adjustment for this SFX (e.g. -3 for quieter, 0 for default)

            Strictly adhere to the established character roles and return ONLY the JSON array structure.
            """
    else:
        context_generated = get_fresh_context(topic)
        prompt_template = f"""
                You are a highly skilled scriptwriter for short-form social media comedy, specializing in creating structured Top 5 lists and debates.
    
                **PRIMARY INSTRUCTION:** Generate a dialogue script about a "Top 5 List" between two distinct personalities, Nina and Tina. The entire script must be **in English** and follow the structured JSON format provided.
    
                **TOPIC:** The Top 5 {topic}.
                **CONTEXT:{context_generated}**
    
                **STRUCTURED DEBATE FLOW:**
                The script MUST follow a structure where the list is presented, and Nina challenges the ranking/inclusion of at least 3 items.
                1.  **OPENING:** Casual greeting/topic setup. (1-2 lines but consider more if the line had to broken in multiple lines as per the Json Format rule)
                2.  **ITEMS 5, 4, 3:** Tina presents the item, Nina asks a skeptical/confused question about the item (e.g., "But isn't that too slow?"), and Tina defends the item with an analogy.
                3.  **ITEMS 2, 1:** Tina presents the final items, Nina expresses strong disagreement or surprise, and Tina delivers the final, witty defense.
                4.  **CLOSING:** Nina acknowledges the list, and Tina delivers a casual farewell. (1-2 lines but consider more if the line had to broken in multiple lines as per the Json Format rule)
    
                DURATION: The total read time should aim for at least 250 seconds aproximatedly withing range of plus 20%, consider this will be used for a TTS audio file so the duration could go higher than expected.
    
                **CHARACTERS & TONE:**
                * **Nina (The Skeptical Challenger):** Asks critical questions about the ranking or the drawbacks of an item. Must use contractions (e.g., "don't," "isn't that").
                * **Tina (The Witty Expert & Defender):** Explains the pros of the item using clear, often humorous analogies.
    
                **STYLE REQUIREMENTS:**
                1.  **Language:** ENTIRELY IN ENGLISH.
                2.  **Content:** Include at least one **humorous or simple analogy** from Tina per challenged item.
                3.  **Json Format:** If a dialog is longer than 20 words, break it into multiple lines from the same narrator to keep consitency, the line dialog overall can be over 20 words, we are breaking it just to have short subtitles NOT TO HAVE SHORT DIALOGS(this for short subtitles).
                4. **End**: Finish with a nice casual farewell
                5. **EDITION HIGHLIGHTS:** Identify key moments and tag them with an SFX highlight.
                   - CRITICAL: You may use UP TO {max(1, time_limit // 20)} highlights total — use fewer or none if the
                     script does not have enough genuinely impactful moments. Never place two highlights
                     within 15 seconds of each other.
                   - 'category' MUST be one of: {list(sfx_mapping.keys())}
                   - 'desired_traits' MUST be a list of 2 to 5 descriptive strings for the sound's
                     texture and mood. Draw from or be inspired by this trait catalog:
                     {json.dumps(sfx_mapping, indent=4)}
                   - 'description' MUST be a single natural language sentence describing the exact sound
                     you want (e.g., "a quick cartoon bonk with a spring reverb tail"). This is used
                     as the generation prompt for ElevenLabs when no local asset matches.
                   - 'beat_delay' controls the pause after the SFX plays:
                     'none' = no pause, 'short' = 0.3s, 'long' = 0.7s (use for dramatic effect)
                   - 'placement': 'start' triggers the SFX at the beginning of the segment, 'end' triggers at the end
                   - 'offset_seconds': fine-tune trigger time in seconds (e.g. -0.2 to trigger slightly before)
                   - 'volume_modifier': dB adjustment for this SFX (e.g. -3 for quieter, 0 for default)


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
        # The response text will be a valid JSON string

        # Save the response to a file for debugging purposes
        debug_dir = Path(__file__).parent.parent / "MockScriptFiles"
        debug_dir.mkdir(exist_ok=True)
        sanitized_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '_')).rstrip()
        debug_file_path = debug_dir / f"{sanitized_topic.replace(' ', '_')}.json"
        with open(debug_file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        return response.text

    except Exception as e:
        return f"Error in JSON script generation: {e}"
