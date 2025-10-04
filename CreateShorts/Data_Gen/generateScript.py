from google import genai
from google.genai import types
from CreateShorts.Create_Short_Service.loadEnvData import load_env_data


def generate_interview_script(topic: str) -> str:
    """
    Genera un guion estructurado para un video corto de 45 segundos.
    """
    # 1. El cliente ya está configurado para leer la clave de la variable de entorno
    client = load_env_data(genai.Client, 'GEMINI_API_KEY')

    # 2. Creamos un prompt específico para forzar la estructura
    prompt = f"""
    Eres un experto en reclutamiento de SDE II en Amazon. Genera un guion para un video de 45 segundos (máximo 120 palabras) sobre el siguiente tema: "{topic}". 

    El guion debe tener un tono profesional, ser directo y estructurado en estas secciones:
    1. Hook (gancho) de 5 segundos.
    2. Explicación del Error (15 segundos).
    3. Solución Práctica (20 segundos).
    4. El texto debe ser generado en ingles

    Devuelve solo el texto del guion, sin ninguna introducción o etiqueta de sección.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt
        )

        # Devolver el texto del guion
        return response.text.strip()

    except Exception as e:
        return f"Error en la generación del guion: {e}"


if __name__ == "__main__":
    tema = "No saber cómo manejar el principio de liderazgo 'Dive Deep' en una entrevista."
    script = generate_interview_script(tema)

    print("\n--- GUION GENERADO ---")
    print(f"Tema: {tema}")
    print("-" * 50)
    print(script)
    print("-" * 50)
    print(f"Total de caracteres: {len(script)}")