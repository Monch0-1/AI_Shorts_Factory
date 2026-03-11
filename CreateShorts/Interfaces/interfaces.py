from abc import ABC, abstractmethod
from CreateShorts.Models.script_models import ScriptDTO
from CreateShorts.theme_config import ThemeConfig

class IScriptService(ABC):
    @abstractmethod
    def generate(self, topic: str, time_limit: int, theme_config: ThemeConfig,
                 context: str = None, use_template: bool = False, is_monologue: bool = False) -> str:
        pass

class IAudioService(ABC):
    @abstractmethod
    def synthesize(self, script: ScriptDTO, theme: ThemeConfig) -> ScriptDTO:
        pass