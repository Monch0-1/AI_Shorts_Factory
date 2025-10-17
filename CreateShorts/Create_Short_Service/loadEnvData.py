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