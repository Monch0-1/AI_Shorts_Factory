from moviepy.editor import ColorClip

def test_moviepy_is_working():
    # Intenta crear un clip de 1 segundo de color rojo
    try:
        clip = ColorClip(size=(640, 480), color=(255, 0, 0), duration=1)
        # Esto debería funcionar sin errores si FFmpeg está configurado
        print("\n--- ¡ÉXITO! MoviePy e FFmpeg funcionan correctamente. ---")
    except Exception as e:
        print(f"\n--- ERROR ---")
        print(f"El módulo se instaló, pero falló al ejecutar la prueba de clip (problema de FFmpeg o dependencias).")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_moviepy_is_working()