import pytest
from unittest.mock import MagicMock, patch
from google.genai import types
from CreateShorts.Data_Gen.formatter_script import generate_formatter_script_json
from CreateShorts.theme_config import ThemeConfig, PromptingConfig

@pytest.fixture
def mock_theme_config():
    # Use a real schema to satisfy Pydantic validation in google-genai
    script_schema = types.Schema(
        type=types.Type.ARRAY,
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "title": types.Schema(type=types.Type.STRING),
                "content": types.Schema(type=types.Type.STRING)
            }
        )
    )
    
    mock_prompting = MagicMock(spec=PromptingConfig)
    mock_prompting.script_schema = script_schema
    mock_prompting.system_instruction = "Test System Instruction"
    
    config = MagicMock(spec=ThemeConfig)
    config.prompting = mock_prompting
    return config

@patch('CreateShorts.Data_Gen.formatter_script.load_env_data')
def test_generate_formatter_script_json_success(mock_load_env, mock_theme_config):
    # Setup mocks
    mock_client = MagicMock()
    mock_load_env.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.text = '{"parts": [{"title": "Part 1", "content": "Test content"}]}'
    mock_client.models.generate_content.return_value = mock_response
    
    # Execute
    result = generate_formatter_script_json(
        time_limit=60,
        theme_config=mock_theme_config,
        context_story="Once upon a time..."
    )
    
    # Assertions
    assert result == mock_response.text
    mock_client.models.generate_content.assert_called_once()
    
    # Verify prompt contains key elements
    args, kwargs = mock_client.models.generate_content.call_args
    prompt = kwargs['contents']
    assert "250" in prompt
    assert "Once upon a time..." in prompt
    assert "Test System Instruction" in prompt

@patch('CreateShorts.Data_Gen.formatter_script.load_env_data')
def test_generate_formatter_script_json_error(mock_load_env, mock_theme_config):
    # Setup mocks
    mock_client = MagicMock()
    mock_load_env.return_value = mock_client
    
    # Important: The validation happens BEFORE the call reaches our side_effect 
    # if we don't mock correctly. But with a real schema it should be fine.
    mock_client.models.generate_content.side_effect = Exception("API Error")
    
    # Execute
    result = generate_formatter_script_json(
        time_limit=60,
        theme_config=mock_theme_config,
        context_story="Once upon a time..."
    )
    
    # Assertions
    assert "Error in JSON script generation: API Error" in result
