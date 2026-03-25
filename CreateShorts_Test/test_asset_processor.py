"""
Tests for AssetProcessor: normalization (-6dB) and duration cap (3s).
Uses a synthetic audio segment generated with pydub — no real files required.
"""
import os
import pytest
import tempfile
from pydub import AudioSegment
from pydub.generators import Sine
from CreateShorts.Services.AssetProcessor import AssetProcessor, MAX_DURATION_MS, TARGET_DBFS


@pytest.fixture
def processor():
    return AssetProcessor()


def _make_audio_file(duration_ms: int, volume_dbfs: float, suffix: str = ".mp3") -> str:
    """Creates a temporary audio file with the given duration and volume."""
    tone = Sine(440).to_audio_segment(duration=duration_ms)
    # Apply gain to set a known volume level
    gain = volume_dbfs - tone.max_dBFS
    tone = tone.apply_gain(gain)

    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tone.export(tmp.name, format="mp3")
    tmp.close()
    return tmp.name


def test_duration_cap(processor):
    """Files longer than 3s are capped to exactly 3s."""
    path = _make_audio_file(duration_ms=5000, volume_dbfs=-10.0)
    try:
        result = processor.process(path)
        assert result is True
        processed = AudioSegment.from_file(path)
        assert len(processed) <= MAX_DURATION_MS + 50  # 50ms tolerance for mp3 encoding
    finally:
        os.unlink(path)


def test_short_audio_unchanged_duration(processor):
    """Files shorter than 3s are not extended."""
    path = _make_audio_file(duration_ms=1000, volume_dbfs=-10.0)
    try:
        result = processor.process(path)
        assert result is True
        processed = AudioSegment.from_file(path)
        assert len(processed) <= MAX_DURATION_MS
    finally:
        os.unlink(path)


def test_normalization(processor):
    """Audio is normalized to approximately -6dBFS after processing."""
    path = _make_audio_file(duration_ms=1000, volume_dbfs=-20.0)
    try:
        result = processor.process(path)
        assert result is True
        processed = AudioSegment.from_file(path)
        assert abs(processed.max_dBFS - TARGET_DBFS) < 1.5  # 1.5dB tolerance
    finally:
        os.unlink(path)


def test_missing_file_returns_false(processor):
    """Returns False gracefully when the file does not exist."""
    result = processor.process("non_existent_file.mp3")
    assert result is False
