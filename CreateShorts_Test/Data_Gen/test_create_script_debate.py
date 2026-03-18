import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from google.genai import types
from CreateShorts.Data_Gen.create_script_debate import generate_debate_script_json
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

@patch('CreateShorts.Data_Gen.create_script_debate.get_fresh_context')
@patch('CreateShorts.Data_Gen.create_script_debate.ThemeManager')
@patch('CreateShorts.Data_Gen.create_script_debate.load_env_data')
def test_generate_debate_script_json_no_template_success(mock_load_env, mock_theme_manager_class, mock_get_context, mock_theme_config):
    # Setup mocks
    mock_client = MagicMock()
    mock_load_env.return_value = mock_client
    
    mock_theme_manager = mock_theme_manager_class.return_value
    mock_theme_manager.get_sfx_mapping.return_value = {"shock": ["skeptical"], "funny": ["punchline"]}
    
    mock_get_context.return_value = "Mocked Context Data"
    
    mock_response = MagicMock()
    mock_response.text = '[{"speaker": "Nina", "line": "Why?", "tag": "shock"}]'
    mock_client.models.generate_content.return_value = mock_response
    
    # Execute with mock_open to avoid file writing
    with patch("builtins.open", mock_open()):
        result = generate_debate_script_json(
            topic="AI Ethics",
            time_limit=60,
            theme_config=mock_theme_config,
            use_template=False
        )
    
    # Assertions
    assert result == mock_response.text
    mock_client.models.generate_content.assert_called_once()
    
    # Verify prompt contains key elements
    args, kwargs = mock_client.models.generate_content.call_args
    prompt = kwargs['contents']
    assert "AI Ethics" in prompt
    assert "Mocked Context Data" in prompt
    assert "250" in prompt # 60 * 250 / 60 = 250
    assert "shock" in prompt
    assert "skeptical" in prompt

@patch('CreateShorts.Data_Gen.create_script_debate.get_fresh_context')
@patch('CreateShorts.Data_Gen.create_script_debate.ThemeManager')
@patch('CreateShorts.Data_Gen.create_script_debate.load_env_data')
def test_generate_debate_script_json_use_template_success(mock_load_env, mock_theme_manager_class, mock_get_context, mock_theme_config):
    # Setup mocks
    mock_client = MagicMock()
    mock_load_env.return_value = mock_client
    
    mock_theme_manager = mock_theme_manager_class.return_value
    mock_theme_manager.get_sfx_mapping.return_value = {"shock": ["skeptical"], "funny": ["punchline"]}
    
    mock_get_context.return_value = "Mocked Context Data"
    
    mock_response = MagicMock()
    mock_response.text = '[{"speaker": "Tina", "line": "Top 5", "tag": "funny"}]'
    mock_client.models.generate_content.return_value = mock_response
    
    # Execute
    with patch("builtins.open", mock_open()):
        result = generate_debate_script_json(
            topic="Programming Languages",
            time_limit=60,
            theme_config=mock_theme_config,
            use_template=True
        )
    
    # Assertions
    assert result == mock_response.text
    mock_client.models.generate_content.assert_called_once()
    
    # Verify template-specific prompt elements
    args, kwargs = mock_client.models.generate_content.call_args
    prompt = kwargs['contents']
    assert "The Top 5 Programming Languages" in prompt
    assert "STRUCTURED DEBATE FLOW" in prompt
    assert "shock" in prompt

@patch('CreateShorts.Data_Gen.create_script_debate.load_env_data')
def test_generate_debate_script_json_error(mock_load_env, mock_theme_config):
    # Setup mocks
    mock_client = MagicMock()
    mock_load_env.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception("API Error")
    
    # Execute
    # We don't need to patch ThemeManager here because it's initialized after load_env_data
    # but before the try-except. To be safe, let's patch it and provide mapping.
    with patch('CreateShorts.Data_Gen.create_script_debate.ThemeManager') as mock_tm_class:
        mock_tm_class.return_value.get_sfx_mapping.return_value = {"test": ["tag"]}
        result = generate_debate_script_json(
            topic="Error Test",
            time_limit=60,
            theme_config=mock_theme_config
        )
    
    # Assertions
    assert "Error in JSON script generation: API Error" in result
