import unittest
import os
import wave
import numpy as np
from moviepy.editor import AudioFileClip
from pydub import AudioSegment
import io

import subprocess
import os
from pydub.utils import which


def verify_ffmpeg_setup():
    """
    Verifica la configuración de FFmpeg e imprime información de diagnóstico
    """
    print("=== Diagnóstico de FFmpeg ===")

    # Verificar si FFmpeg está en el PATH
    ffmpeg_path = which("ffmpeg")
    print(f"Ruta de FFmpeg encontrada: {ffmpeg_path}")

    # Verificar variable PATH
    print("\nVariable PATH:")
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    for dir in path_dirs:
        if 'ffmpeg' in dir.lower():
            print(f"Directorio FFmpeg en PATH: {dir}")

    # Intentar ejecutar FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                                capture_output=True,
                                text=True)
        print("\nVersión de FFmpeg:")
        print(result.stdout.split('\n')[0])
        return True
    except Exception as e:
        print(f"\nError al ejecutar FFmpeg: {e}")
        return False


# Ejecutar la verificación
if not verify_ffmpeg_setup():
    print("Por favor, asegúrate de que FFmpeg está correctamente instalado y en el PATH")


def create_test_audio_chunk(duration_ms=500, sample_rate=44100):
    """
    Crea un chunk de audio de prueba
    """
    t = np.linspace(0, duration_ms / 1000, int(sample_rate * duration_ms / 1000))
    frequency = 440  # 440 Hz (nota La)
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_int16 = (audio_data * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes por muestra
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

    return buffer.getvalue()


def assemble_dialogue_pydub(audio_chunks, output_filename):
    """
    Ensambla chunks de audio en un solo archivo
    """
    if not audio_chunks:
        return None

    # Crear el primer segmento
    combined = AudioSegment.empty()

    for chunk in audio_chunks:
        # Convertir el chunk de bytes a un objeto AudioSegment
        chunk_buffer = io.BytesIO(chunk)
        segment = AudioSegment.from_wav(chunk_buffer)
        combined += segment

    # Exportar el resultado
    combined.export(output_filename, format="mp3")
    return output_filename


class TestAssembleDialoguePydub(unittest.TestCase):
    def setUp(self):
        # Crear directorio temporal para las pruebas
        self.test_output_dir = "test_output"
        if not os.path.exists(self.test_output_dir):
            os.makedirs(self.test_output_dir)

        # Crear chunks de audio de prueba
        self.audio_chunks = [
            create_test_audio_chunk(500),  # 500ms
            create_test_audio_chunk(300),  # 300ms
            create_test_audio_chunk(700)  # 700ms
        ]

        self.output_filename = os.path.join(self.test_output_dir, "test_output.mp3")

    def tearDown(self):
        # Limpiar archivos de prueba
        if os.path.exists(self.output_filename):
            os.remove(self.output_filename)
        if os.path.exists(self.test_output_dir):
            os.rmdir(self.test_output_dir)

    def test_assemble_dialogue_basic(self):
        # Probar la función principal
        result_path = assemble_dialogue_pydub(self.audio_chunks, self.output_filename)

        # Verificar que el archivo existe
        self.assertTrue(os.path.exists(result_path))

        # Verificar que el archivo de audio se puede abrir y tiene contenido
        audio = AudioFileClip(result_path)

        # La duración total debería ser aproximadamente 1.5 segundos (500 + 300 + 700 ms)
        expected_duration = 1.5  # segundos
        self.assertAlmostEqual(audio.duration, expected_duration, delta=0.1)

        # Limpiar
        audio.close()

    def test_empty_chunks(self):
        # Probar con lista vacía de chunks
        result_path = assemble_dialogue_pydub([], self.output_filename)
        self.assertIsNone(result_path)  # O el comportamiento que esperas para chunks vacíos

    def test_invalid_chunk(self):
        # Probar con datos de audio inválidos
        invalid_chunks = [b'not an audio file']
        with self.assertRaises(Exception):  # Ajusta la excepción específica según tu implementación
            assemble_dialogue_pydub(invalid_chunks, self.output_filename)


if __name__ == '__main__':
    unittest.main()