from google import genai
from google.genai import types
from CreateShorts.Data_Gen.create_monologe import generate_monologue_script
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.Create_Short_Service.loadEnvData import load_env_data


def generate_script(topic: str, time: int, isMonologe: bool, context: str = None) -> str:


    if isMonologe:
        return generate_monologue_script(str, time)

    else:
        return generate_debate_script_json(topic, time)
