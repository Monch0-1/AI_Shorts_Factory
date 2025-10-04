# import os
# from google import genai
# from elevenlabs.client import ElevenLabs
# from dotenv import load_dotenv # ⬅️ NUEVA IMPORTACIÓN
# from google.genai import Client
#
# load_dotenv()
#
# # LEER LA CLAVE EXPLÍCITAMENTE
# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
#
# # Verificar si la clave se encontró antes de intentar usarla
# if not GEMINI_API_KEY:
#     print("ERROR FATAL: La clave ELEVEN_API_KEY no se encontró en el entorno.")
#     exit()
#
# try:
#     # CORRECCIÓN CLAVE: Pasamos la clave directamente al constructor
#     client = genai.Client(api_key=GEMINI_API_KEY)
#
# except Exception:
#     # Este bloque solo se alcanza si el cliente no se inicializa por otras razones
#     print("ERROR: Fallo al inicializar genai Client.")
#     exit()


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

# Ejemplo de uso en generateScript.py:
# from CreateShorts.Create_Short_Service.loadEnvData import load_env_data
# client = load_env_data(genai.Client, 'GEMINI_API_KEY')