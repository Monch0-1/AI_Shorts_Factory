import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Set
from google.genai import types
from CreateShorts.utils import get_project_root
from CreateShorts.Data_Gen.eleven_labs_voice_settings_config import ElevenLabsVoiceSettings

@dataclass
class PromptingConfig:
    system_instruction: str
    script_schema: types.Schema
    refinement_goal: str
    target_quality_rules: List[str] = field(default_factory=list)
    best_examples: List[str] = field(default_factory=list)

@dataclass
class ThemeConfig:
    name: str
    video_paths: List[str]
    music_path: str
    music_volume: float
    prompting: PromptingConfig
    resources: Dict = field(default_factory=dict)
    voice_settings: Optional[ElevenLabsVoiceSettings] = None


def _get_default_system_instruction():
    return """
    You are a highly skilled scriptwriter for short-form social media comedy and tech debates.
    Your primary goal is to write a casual, witty, and engaging dialogue strictly between two characters.
    Nina must pose skeptical, common-sense questions to expose flaws.
    Tina must provide clear, witty, and often funny analogies to explain complex concepts simply.
    The conversation must flow naturally without lecturing the audience.
    """

def _create_schema_from_dict(schema_dict: dict) -> types.Schema:
    """Helper para crear un Schema desde un diccionario"""
    if not isinstance(schema_dict, dict):
        raise ValueError("schema_dict debe ser un diccionario")

    schema_type = schema_dict.get('type', 'object')
    description = schema_dict.get('description', '')

    # Manejar propiedades para objetos
    if schema_type == 'object' and 'properties' in schema_dict:
        properties = {}
        for prop_name, prop_schema in schema_dict['properties'].items():
            properties[prop_name] = _create_schema_from_dict(prop_schema)
        
        return types.Schema(
            type=types.Type.OBJECT,
            description=description,
            properties=properties,
            required=schema_dict.get('required', [])
        )
    
    # Manejar arrays
    elif schema_type == 'array' and 'items' in schema_dict:
        items = _create_schema_from_dict(schema_dict['items'])
        return types.Schema(
            type=types.Type.ARRAY,
            description=description,
            items=items
        )
    
    # Manejar tipos primitivos
    else:
        schema_type = getattr(types.Type, schema_type.upper(), types.Type.STRING)
        return types.Schema(
            type=schema_type,
            description=description
        )


def _get_default_schema() -> types.Schema:
    """Retorna un esquema por defecto"""
    return types.Schema(
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


class ThemeManager:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "theme_media_resources.yml"

        self.config_path = config_path
        self.themes: Dict[str, ThemeConfig] = {}
        self.global_resources: Dict = {}
        self._load_config()

    def _load_config(self):
        """Carga la configuración desde el archivo YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            project_root = get_project_root()

            # Load Global Resources
            self.global_resources = config.get('resources', {})
            # No path resolution needed for global resources as they are just tag lists

            # Load Themes
            for theme_name, theme_data in config.get('themes', {}).items():
                try:
                    name = theme_data['name']

                    video_data = theme_data.get('video', {})
                    if 'paths' in video_data:
                        raw_paths = video_data['paths']
                    else:
                        raw_paths = [video_data.get('path')] if 'path' in video_data else []

                    video_paths = [str(project_root / p) for p in raw_paths]
                    music_path = str(project_root / theme_data['music']['path'])
                    music_volume = theme_data['music'].get('volume', 0.10)
                    resources_data = theme_data.get('resources', {})
                    self._resolve_resource_paths(resources_data, project_root)

                    prompting_data = theme_data.get('prompting', {})
                    schema_dict = yaml.safe_load(prompting_data.get('script_schema', '{}'))
                    
                    try:
                        script_schema_obj = _create_schema_from_dict(schema_dict)
                    except Exception as schema_error:
                        print(f"Error creando schema para {theme_name}: {schema_error}")
                        script_schema_obj = _get_default_schema()

                    prompting_config = PromptingConfig(
                        system_instruction=prompting_data.get('system_instruction', _get_default_system_instruction()),
                        script_schema=script_schema_obj,
                        refinement_goal=prompting_data.get('refinement_goal', ''),
                        target_quality_rules=prompting_data.get('target_quality_rules', []),
                        best_examples=prompting_data.get('best_examples', [])
                    )

                    # Cargar voice settings
                    voice_settings_data = theme_data.get('voice_settings', {})
                    if voice_settings_data:
                        voice_settings = ElevenLabsVoiceSettings(
                            stability=float(voice_settings_data.get('stability', 0.5)),
                            similarity_boost=float(voice_settings_data.get('similarity_boost', 0.75)),
                            style=float(voice_settings_data.get('style', 0.0)),
                            speed=float(voice_settings_data.get('speed', 1.0)),
                            use_speaker_boost=bool(voice_settings_data.get('use_speaker_boost', True))
                        )
                    else:
                        voice_settings = None

                    self.themes[theme_name] = ThemeConfig(
                        name=name,
                        video_paths=video_paths,
                        music_path=music_path,
                        music_volume=music_volume,
                        prompting=prompting_config,
                        voice_settings=voice_settings,
                        resources = resources_data
                    )

                except Exception as theme_error:
                    print(f"Error cargando tema {theme_name}: {theme_error}")
                    continue

        except Exception as e:
            print(f"Error cargando la configuración: {e}")
            self._load_default_config()

    def _resolve_resource_paths(self, resource_dict: Dict, project_root: Path):
        """Recursively resolve 'path' keys in a dictionary against project_root"""
        for key, value in resource_dict.items():
            if isinstance(value, dict):
                self._resolve_resource_paths(value, project_root)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and 'path' in item:
                        item['path'] = str(project_root / item['path'])

    def get_all_available_tags(self) -> List[str]:
        """
        Flattens the global sfx_audio hierarchy to return all unique tags (intents).
        Hierarchy: resources -> sfx_audio -> category -> [tags]
        """
        tags: Set[str] = set()
        sfx_audio = self.global_resources.get('sfx_audio', {})
        
        for category, tag_list in sfx_audio.items():
            if isinstance(tag_list, list):
                for tag in tag_list:
                    tags.add(tag)
        
        return sorted(list(tags))

    def _load_default_config(self):
        project_root = get_project_root()
        default_prompting = PromptingConfig(
            system_instruction=_get_default_system_instruction(),
            script_schema=_get_default_schema()
        )

        self.themes['default'] = ThemeConfig(
            name="default",
            video_paths=[str(project_root / "resources/video/4.mp4")],
            music_path=str(project_root / "resources/audio/2_23_AM.mp3"),
            music_volume=0.10,
            prompting=default_prompting
        )

    def get_theme_config(self, theme_name: str) -> ThemeConfig:
        """Obtiene la configuración para un tema específico"""
        return self.themes.get(theme_name, self.themes['default'])
