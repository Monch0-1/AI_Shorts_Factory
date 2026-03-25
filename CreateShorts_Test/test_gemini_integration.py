import pytest
import os
import json
from CreateShorts.Data_Gen.create_script_monologue import generate_monolog_script_json
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
from CreateShorts.theme_config import ThemeManager

# Only run if RUN_GEMINI_TESTS=true
run_gemini = os.getenv("RUN_GEMINI_TESTS", "false").lower() == "true"

@pytest.mark.skipif(not run_gemini, reason="Skipping Gemini API tests to save tokens. Set RUN_GEMINI_TESTS=true to run.")
@pytest.mark.gemini_test
class TestGeminiScriptGeneration:
    
    @pytest.fixture
    def theme_manager(self):
        return ThemeManager()

    def test_generate_monologue_horror_with_highlights(self, theme_manager):
        """
        Validates that the horror monologue generator returns valid JSON 
        and includes the 'highlight' field in at least some segments.
        """
        theme = theme_manager.get_theme_config("horror")
        topic = "A person hears their own voice calling them from the basement, but they are alone."
        
        # Calling the real Gemini API
        response_text = generate_monolog_script_json(
            final_script_prompt=f"Create a horror story about: {topic}",
            time_limit=45,
            theme_config=theme
        )
        
        assert isinstance(response_text, str), "Response should be a string"
        script_data = json.loads(response_text)
        assert isinstance(script_data, list), "Response should be a JSON array"
        assert len(script_data) > 0, "Script should not be empty"
        
        has_highlight = False
        for segment in script_data:
            assert "speaker" in segment
            assert "line" in segment
            # The horror schema in theme_media_resources.yml requires 'mood'
            assert "mood" in segment
            
            if "highlight" in segment:
                highlight = segment["highlight"]
                # Required schema fields
                assert "category" in highlight
                assert "desired_traits" in highlight
                assert isinstance(highlight["desired_traits"], list)
                assert "placement" in highlight
                assert highlight["placement"] in ["start", "end"]
                # Optional fields — only validate type if present
                if "offset_seconds" in highlight:
                    assert isinstance(highlight["offset_seconds"], (int, float))
                if "volume_modifier" in highlight:
                    assert isinstance(highlight["volume_modifier"], (int, float))
                has_highlight = True
        
        assert has_highlight, "Horror script should contain at least one highlight/SFX marker"

    def test_generate_debate_debate_with_highlights(self, theme_manager):
        """
        Validates that the debate generator (Nina vs Tina) returns valid JSON
        and includes highlights for 'shock' or 'funny' moments.
        """
        theme = theme_manager.get_theme_config("default") 
        topic = "Why you shouldn't use production as a test environment"
        
        # Calling the real Gemini API
        response_text = generate_debate_script_json(
            topic=topic,
            time_limit=60,
            theme_config=theme,
            use_template=False
        )
        
        assert isinstance(response_text, str)
        assert not response_text.startswith("Error"), f"Gemini returned an error: {response_text}"
        script_data = json.loads(response_text)
        assert isinstance(script_data, list)
        assert len(script_data) > 0

        valid_speakers = ["Nina", "Tina"]
        has_highlight = False

        for segment in script_data:
            assert "speaker" in segment
            assert segment["speaker"] in valid_speakers
            assert "line" in segment
            assert "topic" in segment

            if "highlight" in segment:
                highlight = segment["highlight"]
                # Required schema fields
                assert "category" in highlight
                assert "desired_traits" in highlight
                assert isinstance(highlight["desired_traits"], list)
                assert "placement" in highlight
                # Optional fields — only validate type if present
                if "offset_seconds" in highlight:
                    assert isinstance(highlight["offset_seconds"], (int, float))
                if "volume_modifier" in highlight:
                    assert isinstance(highlight["volume_modifier"], (int, float))
                has_highlight = True
                
        assert has_highlight, "Debate script should contain at least one highlight marker (funny/shock)"
