import json
import pytest
from unittest.mock import MagicMock, patch
from google.genai import types
from CreateShorts.Data_Gen.create_script_monologue import generate_monolog_script_json
from CreateShorts.theme_config import ThemeConfig, PromptingConfig

@pytest.fixture
def mock_theme_config():
    # Use a real schema to satisfy Pydantic validation
    script_schema = types.Schema(
        type=types.Type.ARRAY,
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "speaker": types.Schema(type=types.Type.STRING),
                "line": types.Schema(type=types.Type.STRING),
                "tag": types.Schema(type=types.Type.STRING)
            }
        )
    )
    
    mock_prompting = MagicMock(spec=PromptingConfig)
    mock_prompting.script_schema = script_schema
    mock_prompting.system_instruction = "Test System Instruction"
    
    config = MagicMock(spec=ThemeConfig)
    config.prompting = mock_prompting
    return config

@patch('CreateShorts.Data_Gen.create_script_monologue.ThemeManager')
@patch('CreateShorts.Data_Gen.create_script_monologue.load_env_data')
def test_generate_monolog_script_json_success(mock_load_env, mock_theme_manager_class, mock_theme_config):
    # Setup mocks
    mock_client = MagicMock()
    mock_load_env.return_value = mock_client
    
    mock_theme_manager = mock_theme_manager_class.return_value
    mock_theme_manager.get_sfx_mapping.return_value = {"horror": ["jump_scare"], "comedy": ["punchline"]}
    
    mock_response = MagicMock()
    mock_response.text = '[{"speaker": "Narrator_Male", "line": "Test line", "tag": "funny"}]'
    mock_client.models.generate_content.return_value = mock_response
    
    # Execute
    result = generate_monolog_script_json(
        final_script_prompt="Write a story about a cat.",
        time_limit=60,
        theme_config=mock_theme_config,
        context="A funny cat story."
    )
    
    # Assertions
    assert result == mock_response.text
    mock_client.models.generate_content.assert_called_once()
    
    # Verify prompt contains key elements
    args, kwargs = mock_client.models.generate_content.call_args
    prompt = kwargs['contents']
    assert "Write a story about a cat." in prompt
    assert "60" in prompt
    assert '"horror": [\n                     "jump_scare"\n                   ]' in prompt or "horror" in prompt
    assert "Narrator_Male" in prompt
    assert "The 'type' property MUST be one of the Categories" in prompt

@patch('CreateShorts.Data_Gen.create_script_monologue.ThemeManager')
@patch('CreateShorts.Data_Gen.create_script_monologue.load_env_data')
def test_generate_monolog_script_json_error(mock_load_env, mock_theme_manager_class, mock_theme_config):
    # Setup mocks
    mock_client = MagicMock()
    mock_load_env.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception("API Error")
    
    mock_theme_manager = mock_theme_manager_class.return_value
    mock_theme_manager.get_sfx_mapping.return_value = {"test": ["tag"]}
    
    # Execute
    result = generate_monolog_script_json(
        final_script_prompt="Write a story about a cat.",
        time_limit=60,
        theme_config=mock_theme_config
    )
    
    # Assertions
    assert "Error in JSON script generation: API Error" in result
