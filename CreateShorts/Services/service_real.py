from CreateShorts.Interfaces.interfaces import IAudioService, IScriptService
from CreateShorts.Data_Gen.text_to_speach import generate_script_audio_v2
from CreateShorts.Models.script_models import ScriptDTO
from CreateShorts.Data_Gen.create_script_monologue import generate_monolog_script_json
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Prompt_Refinig_Service.refine_base_prompt import refine_base_prompt
from CreateShorts.theme_config import ThemeConfig

class RealAudioService(IAudioService):
    def synthesize(self, script: ScriptDTO, theme: ThemeConfig) -> ScriptDTO:
        print("💰 [REAL MODE] Calling ElevenLabs via text_to_speach.py...")
        return generate_script_audio_v2(script, theme)


class RealScriptService(IScriptService):
    def generate(self, topic: str, time_limit: int, theme_config: ThemeConfig,
                 context: str = None, use_template: bool = False, is_monologue: bool = False,
                 enable_refiner: bool = False) -> str:

        print("💰 [REAL MODE] Calling Gemini API...")

        if is_monologue:
            # Only use the refiner if explicitly enabled
            if enable_refiner:
                print("✨ [PROMPT REFINER] Refining base prompt...")
                final_prompt = refine_base_prompt(topic, theme_config, False)
            else:
                print("⏩ [PROMPT REFINER] Skipped. Using topic directly.")
                final_prompt = topic

            return generate_monolog_script_json(
                final_script_prompt=final_prompt,
                time_limit=time_limit,
                theme_config=theme_config,
                context=context
            )
        else:
            return generate_debate_script_json(
                topic=topic,
                time_limit=time_limit,
                theme_config=theme_config,
                use_template=use_template,
                context=context
            )