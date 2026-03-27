"""
Tests for SFXService coordinator: local hit, local miss → AI fallback, both fail.
"""
import pytest
from unittest.mock import MagicMock
from CreateShorts.Services.SFXService import SFXService


def _make_service(local_result, ai_result):
    local = MagicMock()
    local.get_sfx.return_value = local_result
    ai = MagicMock()
    ai.get_sfx.return_value = ai_result
    return SFXService(local_provider=local, ai_provider=ai), local, ai


def test_local_hit_returns_immediately():
    """If LocalSFXProvider returns a path, AI provider is never called."""
    service, local, ai = _make_service("sfx/comedy/bonk.mp3", None)

    result = service.get_sfx_path("comedy", ["bonk"])

    assert result == "sfx/comedy/bonk.mp3"
    local.get_sfx.assert_called_once_with("comedy", ["bonk"])
    ai.get_sfx.assert_not_called()


def test_local_miss_triggers_ai_fallback():
    """If LocalSFXProvider returns None, ElevenLabsSFXProvider is called."""
    service, local, ai = _make_service(None, "sfx/comedy/generated/gen_abc123.mp3")

    result = service.get_sfx_path("comedy", ["silly", "fast"])

    assert result == "sfx/comedy/generated/gen_abc123.mp3"
    local.get_sfx.assert_called_once()
    ai.get_sfx.assert_called_once_with("comedy", ["silly", "fast"], None)


def test_both_fail_returns_none():
    """If both providers return None, the service returns None."""
    service, local, ai = _make_service(None, None)

    result = service.get_sfx_path("horror", ["sharp"])

    assert result is None
    local.get_sfx.assert_called_once()
    ai.get_sfx.assert_called_once()


def test_correct_args_passed_to_providers():
    """Category and desired_traits are forwarded unchanged to both providers."""
    service, local, ai = _make_service(None, None)

    service.get_sfx_path("neutral", ["clean", "soft", "gentle"])

    local.get_sfx.assert_called_once_with("neutral", ["clean", "soft", "gentle"])
    ai.get_sfx.assert_called_once_with("neutral", ["clean", "soft", "gentle"], None)


def test_none_category_returns_none_immediately():
    """None or empty category skips both providers and returns None."""
    service, local, ai = _make_service("sfx/comedy/bonk.mp3", "sfx/comedy/gen.mp3")

    assert service.get_sfx_path(None, ["bonk"]) is None
    assert service.get_sfx_path("", ["bonk"]) is None
    local.get_sfx.assert_not_called()
    ai.get_sfx.assert_not_called()


def test_description_forwarded_to_ai_provider():
    """Description is forwarded to the AI provider when local lookup fails."""
    service, local, ai = _make_service(None, "sfx/comedy/generated/gen_xyz.mp3")

    result = service.get_sfx_path("comedy", ["silly"], "a quick silly cartoon boing sound")

    assert result == "sfx/comedy/generated/gen_xyz.mp3"
    ai.get_sfx.assert_called_once_with("comedy", ["silly"], "a quick silly cartoon boing sound")
