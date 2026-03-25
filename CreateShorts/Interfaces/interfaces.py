from abc import ABC, abstractmethod
from typing import List, Optional
from CreateShorts.Models.script_models import ScriptDTO
from CreateShorts.theme_config import ThemeConfig


class IScriptService(ABC):
    @abstractmethod
    def generate(self, topic: str, time_limit: int, theme_config: ThemeConfig,
                 context: str = None, use_template: bool = False, is_monologue: bool = False,
                 enable_refiner: bool = False) -> str:
        pass


class IAudioService(ABC):
    @abstractmethod
    def synthesize(self, script: ScriptDTO, theme: ThemeConfig) -> ScriptDTO:
        pass


class ISFXProvider(ABC):
    """
    Abstract interface for SFX asset selection sources.
    Implementations: LocalSFXProvider (DB scoring), ElevenLabsSFXProvider (AI generation).
    """
    @abstractmethod
    def get_sfx(self, category: str, desired_traits: List[str]) -> Optional[str]:
        """
        Returns the file path of a suitable SFX asset, or None if unavailable.

        :param category: Primary SFX category (e.g., 'comedy', 'horror', 'neutral')
        :param desired_traits: Descriptive trait strings (e.g., ['bonk', 'cartoon', 'fast'])
        :return: Absolute or relative file path, or None.
        """
        pass