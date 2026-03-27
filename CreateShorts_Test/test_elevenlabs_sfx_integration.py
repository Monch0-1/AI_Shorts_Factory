import os
import pytest
from unittest.mock import MagicMock
from CreateShorts.Services.SFXProviderElevenLabs import ElevenLabsSFXProvider
from CreateShorts.Services.SFXService import SFXService

# Only run if RUN_ELEVENLABS_TESTS=true
run_elevenlabs = os.getenv("RUN_ELEVENLABS_TESTS", "false").lower() == "true"


@pytest.mark.skipif(not run_elevenlabs, reason="Skipping ElevenLabs API tests. Set RUN_ELEVENLABS_TESTS=true to run.")
@pytest.mark.elevenlabs_test
class TestElevenLabsSFXIntegration:

    def test_elevenlabs_provider_returns_file_path(self):
        """
        Calls ElevenLabs sound generation API directly and validates that
        a file path is returned and the generated file exists on disk.
        """
        provider = ElevenLabsSFXProvider()

        assert provider._client is not None, "ElevenLabs client failed to initialize — check ELEVEN_API_KEY in .env"

        result = provider.get_sfx(category="comedy", desired_traits=["bonk", "cartoon"])

        assert result is not None, "ElevenLabs returned None — API call failed or key lacks sound_generation permission"
        assert os.path.exists(result) or os.path.exists(
            os.path.join(os.getcwd(), result)
        ), f"Generated file not found on disk: {result}"

    def test_sfx_service_falls_back_to_elevenlabs(self):
        """
        Validates the full fallback path: local provider returns None,
        SFXService calls ElevenLabs, and a valid file path is returned.
        """
        local_mock = MagicMock()
        local_mock.get_sfx.return_value = None

        service = SFXService(local_provider=local_mock, ai_provider=ElevenLabsSFXProvider())

        result = service.get_sfx_path("comedy", ["bonk", "cartoon"])

        local_mock.get_sfx.assert_called_once_with("comedy", ["bonk", "cartoon"])
        assert result is not None, "Fallback to ElevenLabs failed — check API key and sound_generation permission"
        assert os.path.exists(result) or os.path.exists(
            os.path.join(os.getcwd(), result)
        ), f"Generated file not found on disk: {result}"
