from pathlib import Path

def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    return Path(__file__).parent.parent