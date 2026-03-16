from pathlib import Path
import re

def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    return Path(__file__).parent.parent

def sanitize_filename(name: str) -> str:
    """
    Remueve caracteres no permitidos en nombres de archivos y normaliza el formato.
    Ejemplo: "¿The Shadow People?" -> "the_shadow_people"
    """
    # 1. Convertir a minúsculas y quitar espacios extra
    name = name.lower().strip()

    # 2. Reemplazar espacios por guiones bajos
    name = name.replace(" ", "_")

    # 3. Eliminar cualquier carácter que NO sea alfanumérico o guion bajo
    # Esto elimina ?, !, (, ), ", ', etc.
    name = re.sub(r'[^\w\-]', '', name)

    # 4. Evitar guiones bajos dobles resultantes de la limpieza
    name = re.sub(r'_+', '_', name)

    return name
