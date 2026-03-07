import os
import shutil
from pathlib import Path
from moviepy.editor import AudioFileClip
from CreateShorts.Create_Short_Service.Interfaces.interfaces import IAudioService, IScriptService
from CreateShorts.Create_Short_Service.Models.script_models import ScriptDTO
from CreateShorts.utils import sanitize_filename
from CreateShorts.theme_config import ThemeConfig

# Obtener la ruta del directorio del proyecto de forma más robusta
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Ir 3 niveles arriba desde service_mock.py
TEMP_DIR = PROJECT_ROOT / "TempFiles" / "CreateShorts" / "resources" / "audio" / "temp_audio"
MOCK_DIR = PROJECT_ROOT / "resources" / "audio" / "mocks"


class MockAudioService(IAudioService):
    def synthesize(self, script: ScriptDTO, theme: ThemeConfig) -> ScriptDTO:
        print("🛡️ [MOCK MODE] Simulating Audio using local resources...")
        print(f"🛡️ [DEBUG] MOCK_DIR path: {MOCK_DIR}")
        print(f"🛡️ [DEBUG] MOCK_DIR exists: {MOCK_DIR.exists()}")
        
        # Crear directorios si no existen
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        MOCK_DIR.mkdir(parents=True, exist_ok=True)

        for i, segment in enumerate(script.segments):
            # Buscamos un audio que se llame igual que el speaker (Nina.mp3, Tina.mp3)
            mock_source = MOCK_DIR / f"{segment.speaker}.mp3"

            # Si no existe, usamos un "fallback.mp3" que tengas ahí
            if not mock_source.exists():
                mock_source = MOCK_DIR / "fallback.mp3"
                print(f"🛡️ [DEBUG] Using fallback: {mock_source}")
                print(f"🛡️ [DEBUG] Fallback exists: {mock_source.exists()}")

            file_name = f"mock_seg_{i}_{segment.speaker}.mp3"
            chunk_path = TEMP_DIR / file_name

            # Verificar que el archivo fuente existe antes de copiarlo
            if not mock_source.exists():
                print(f"❌ [ERROR] Mock source file not found: {mock_source}")
                print(f"💡 [INFO] Available files in MOCK_DIR:")
                if MOCK_DIR.exists():
                    for file in MOCK_DIR.iterdir():
                        print(f"   - {file.name}")
                else:
                    print("   - Directory does not exist!")
                continue

            try:
                # En lugar de API, copiamos el archivo local
                shutil.copy(str(mock_source), str(chunk_path))

                # Obtenemos la duración real del archivo copiado
                with AudioFileClip(str(chunk_path)) as audio_clip:
                    segment.duration = audio_clip.duration

                segment.audio_path = str(chunk_path)
                print(f"   [MOCK OK] {segment.duration:.2f}s | Path: {file_name}")
                
            except Exception as e:
                print(f"❌ [ERROR] Failed to process {segment.speaker}: {e}")

        return script


class MockScriptService(IScriptService):
    def generate(self, topic: str, time_limit: int, theme_config: ThemeConfig,
                 context: str = None, use_template: bool = False, is_monologue: bool = False) -> str:
        # Usar rutas absolutas también aquí
        debug_scripts_dir = PROJECT_ROOT / "debug_scripts"
        
        # Intentamos buscar un archivo que coincida con el tópico
        sanitized_topic = sanitize_filename(topic)
        mock_path = debug_scripts_dir / f"{sanitized_topic}.json"

        # Fallback si no existe el archivo específico
        if not mock_path.exists():
            fallback_path = debug_scripts_dir / "5_Everyday_Myths_You_Still_Believe_But_Arent_True.json"
            if fallback_path.exists():
                mock_path = fallback_path
            else:
                print(f"❌ [ERROR] No mock scripts found in: {debug_scripts_dir}")
                return '[]'  # Retornar script vacío como fallback

        print(f"🛡️ [MOCK MODE] Reading local script: {mock_path}")
        try:
            with open(mock_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"❌ [ERROR] Failed to read script: {e}")
            return '[]'