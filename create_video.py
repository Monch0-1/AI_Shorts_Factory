from moviepy.editor import *

def get_absolute_path(filename):
    # Esto construye la ruta absoluta del archivo
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

def create_short_video(audio_path, image_path, output_path):
    # 1. Cargar el clip de audio
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration

    # 2. Cargar una imagen de fondo (o video)
    # Usamos ImageClip y establecemos su duración para que coincida con el audio
    # Nota: Asegúrate de tener una imagen llamada 'background.jpg' en el directorio
    image_clip = ImageClip(image_path).set_duration(audio_duration)

    # 3. Adjuntar el audio al clip de video
    video_clip = image_clip.set_audio(audio_clip)

    # 4. Exportar el video final (sin subtítulos, por ahora)
    print("-> Renderizando video...")
    video_clip.write_videofile(
        output_path,
        fps=24,  # Frames por segundo estándar
        codec='libx264',  # Codec estándar para MP4
        audio_codec='aac'
    )
    print(f"-> Video finalizado: {output_path}")

if __name__ == "__main__":
    audio_file = get_absolute_path(".venv/Scripts/guion_entrevista_sde.mp3")
    image_file = get_absolute_path(".venv/Scripts/background.jpg")
    output_file = get_absolute_path("final_short.mp4")

    # 🚨 Importante: Debes ejecutar este script desde la raíz del proyecto
    create_short_video(audio_file, image_file, output_file)