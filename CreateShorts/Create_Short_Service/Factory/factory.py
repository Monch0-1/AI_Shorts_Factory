import os

from dotenv import load_dotenv
from CreateShorts.Create_Short_Service.Services.service_real import RealScriptService, RealAudioService
from CreateShorts.Create_Short_Service.Services.service_mock import MockScriptService, MockAudioService

load_dotenv()

def get_script_provider():
    mode = os.getenv("APP_MODE", "DEBUG")
    return RealScriptService() if mode == "PROD" else MockScriptService()


def get_audio_provider():
    mode = os.getenv("APP_MODE", "DEBUG").upper()
    return RealAudioService() if mode == "PROD" else MockAudioService()