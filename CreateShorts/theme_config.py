import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional
from google.genai import types
from CreateShorts.utils import get_project_root


@dataclass
class PromptingConfig:
    system_instruction: str
    script_schema: types.Schema

@dataclass
class ThemeConfig:
    video_path: str
    music_path: str
    music_volume: float
    prompting: PromptingConfig

class ThemeManager:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "theme_media_resources.yml"

        self.config_path = config_path
        self.themes: Dict[str, ThemeConfig] = {}
        self._load_config()

    def _load_config(self):
        """Carga la configuración desde el archivo YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            project_root = get_project_root()

            for theme_name, theme_data in config['themes'].items():
                video_path = str(project_root / "CreateShorts" / theme_data['video']['path'])
                music_path = str(project_root / "CreateShorts" / theme_data['music']['path'])
                music_volume = theme_data['music'].get('volume', 0.10)

                prompting_data = theme_data.get('prompting', {})
                prompting_config = PromptingConfig(
                    system_instruction=prompting_data.get('system_instruction', self._get_default_system_instruction()),
                    script_schema=types.Schema(
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
                )

                print(f"Loading theme '{theme_name}':")
                print(f"Video path: {video_path}")
                print(f"Music path: {music_path}")
                print(f"Volume: {music_volume}")

                # Verificar que los archivos existen
                if not Path(video_path).exists():
                    print(f"Warning: Video file not found: {video_path}")
                if not Path(music_path).exists():
                    print(f"Warning: Music file not found: {music_path}")

                self.themes[theme_name] = ThemeConfig(
                    video_path=video_path,
                    music_path=music_path,
                    music_volume=music_volume,
                    prompting=prompting_config
                )
        except Exception as e:
            print(f"Error cargando la configuración: {e}")
            self._load_default_config()

    def _load_default_config(self):
        """Carga una configuración por defecto si falla la carga del archivo"""
        project_root = get_project_root()
        default_prompting = PromptingConfig(
            system_instruction=self._get_default_system_instruction(),
            script_schema=types.Schema(
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
        )

        self.themes['default'] = ThemeConfig(
            video_path=str(project_root / "CreateShorts/resources/video/4.mp4"),
            music_path=str(project_root / "CreateShorts/resources/audio/2_23_AM.mp3"),
            music_volume=0.10,
            prompting=default_prompting
        )

    def _get_default_system_instruction(self):
        return """
        You are a highly skilled scriptwriter for short-form social media comedy and tech debates.
        Your primary goal is to write a casual, witty, and engaging dialogue strictly between two characters.
        Nina must pose skeptical, common-sense questions to expose flaws.
        Tina must provide clear, witty, and often funny analogies to explain complex concepts simply.
        The conversation must flow naturally without lecturing the audience.
        """

    def get_theme_config(self, theme_name: str) -> ThemeConfig:
        """Obtiene la configuración para un tema específico"""
        return self.themes.get(theme_name, self.themes['default'])