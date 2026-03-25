import logging
from pathlib import Path
from pydub import AudioSegment
from CreateShorts.config import SFX_MAX_DURATION_MS as MAX_DURATION_MS, SFX_TARGET_DBFS as TARGET_DBFS

logger = logging.getLogger(__name__)


class AssetProcessor:
    """
    Pre-processes SFX audio assets before ingestion (RT1).
    - Normalizes peak volume to -6dB
    - Caps duration at 3.0 seconds
    """

    def process(self, file_path: str) -> bool:
        """
        Normalizes and caps the audio file in-place.

        :param file_path: Absolute or relative path to the audio file.
        :return: True if processing succeeded, False otherwise.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"AssetProcessor: File not found: {file_path}")
            return False

        try:
            audio = AudioSegment.from_file(str(path))

            # 1. Cap duration at 3.0s
            if len(audio) > MAX_DURATION_MS:
                audio = audio[:MAX_DURATION_MS]
                logger.info(f"AssetProcessor: Capped '{path.name}' to {MAX_DURATION_MS}ms")

            # 2. Normalize peak to -6dB
            peak_dbfs = audio.max_dBFS
            if peak_dbfs != float('-inf'):
                gain_needed = TARGET_DBFS - peak_dbfs
                audio = audio.apply_gain(gain_needed)
                logger.info(f"AssetProcessor: Normalized '{path.name}' by {gain_needed:+.1f}dB (peak was {peak_dbfs:.1f}dBFS)")

            # 3. Export back in-place (preserve original format)
            suffix = path.suffix.lower().lstrip(".")
            fmt = "mp3" if suffix == "mp3" else suffix
            audio.export(str(path), format=fmt)

            return True

        except Exception as e:
            logger.error(f"AssetProcessor: Failed to process '{file_path}': {e}")
            return False
