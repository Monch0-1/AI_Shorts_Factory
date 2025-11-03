import os
from dotenv import load_dotenv
from google import genai
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

def load_env_data(client_class, keyword):
    # Cargar el archivo .env (asegurando que busque en la raiz del proyecto)
    # Nota: No olvides instalar python-dotenv
    load_dotenv()

    API_KEY = os.getenv(keyword)

    if not API_KEY:
        # Lanza una excepción clara si falta la clave de entorno
        raise ValueError(f"ERROR: La clave {keyword} no se encontró en el entorno. Verifica tu archivo .env.")

    try:
        # Pasa la clave directamente al constructor de la clase cliente
        client = client_class(api_key=API_KEY)
        return client

    except Exception as e:
        # Lanza una excepción más específica si la inicialización falla
        raise RuntimeError(f"ERROR al inicializar {client_class.__name__}: {e}")


# CreateShorts/Create_Short_Service/load_env_data.py (o un nuevo módulo utils)

# Asegúrate de llamar a load_dotenv() al inicio de tu aplicación

def load_unified_assets() -> dict:
    """
    [DEPRECATED: Usar esta función en código nuevo, reemplazar la antigua load_env_data]
    Inicializa todos los clientes de API y recolecta las claves de entorno necesarias
    para la Fábrica de Contenido (Gemini, ElevenLabs, Google Search).
    """

    # 1. Obtener Credenciales
    # Usamos la clave de Gemini como base, si no hay clave de búsqueda específica
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", GEMINI_API_KEY)
    SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    # 2. Inicializar Clientes (Usando las claves del entorno)
    gemini_client = None
    search_service = None

    try:
        # Cliente de Gemini
        gemini_client = genai.Client()
    except Exception as e:
        print(f"ERROR: No se pudo inicializar Gemini Client. {e}")

    # Cliente de Google Custom Search
    if SEARCH_API_KEY and SEARCH_ENGINE_ID:
        try:
            search_service = build("customsearch", "v1", developerKey=SEARCH_API_KEY)
        except Exception as e:
            print(f"ERROR: No se pudo inicializar Google Search API Client: {e}")

    # 3. Retornar el diccionario de activos
    return {
        'GEMINI_CLIENT': gemini_client,
        'SEARCH_SERVICE': search_service,
        'SEARCH_API_KEY': SEARCH_API_KEY,
        'SEARCH_ENGINE_ID': SEARCH_ENGINE_ID,  # El valor 'cx'
    }

load_dotenv()