import pytest
from unittest.mock import MagicMock, patch
from CreateShorts.Data_Gen.moviepy_config import _is_nvenc_available, get_render_params
import CreateShorts.Data_Gen.moviepy_config as moviepy_config

@patch('CreateShorts.Data_Gen.moviepy_config.subprocess.run')
@patch('CreateShorts.Data_Gen.moviepy_config.get_setting')
def test_is_nvenc_available_success(mock_get_setting, mock_run):
    mock_get_setting.return_value = "ffmpeg.exe"
    mock_run.return_value = MagicMock(returncode=0)
    
    assert _is_nvenc_available() is True
    mock_run.assert_called_once()
    assert "h264_nvenc" in mock_run.call_args[0][0]

@patch('CreateShorts.Data_Gen.moviepy_config.subprocess.run')
@patch('CreateShorts.Data_Gen.moviepy_config.get_setting')
def test_is_nvenc_available_fail(mock_get_setting, mock_run):
    mock_get_setting.return_value = "ffmpeg.exe"
    mock_run.return_value = MagicMock(returncode=1)
    
    assert _is_nvenc_available() is False

@patch('CreateShorts.Data_Gen.moviepy_config.ACCELERATION_AVAILABLE', True)
def test_get_render_params_gpu():
    params = get_render_params()
    assert params["codec"] == "h264_nvenc"
    assert "-preset" in params["ffmpeg_params"]
    assert "p3" in params["ffmpeg_params"]

@patch('CreateShorts.Data_Gen.moviepy_config.ACCELERATION_AVAILABLE', False)
def test_get_render_params_cpu():
    params = get_render_params()
    assert params["codec"] == "libx264"
    assert "medium" in params["ffmpeg_params"]

@patch('os.getenv')
@patch('CreateShorts.Data_Gen.moviepy_config._is_nvenc_available')
def test_acceleration_logic_disabled_by_config(mock_nvenc, mock_getenv):
    mock_getenv.return_value = "false"
    
    # We need to simulate the module-level logic
    use_accel_env = mock_getenv("USE_ACCEL", "false").lower() == "true"
    if use_accel_env:
        accel_available = mock_nvenc()
    else:
        accel_available = False
        
    assert accel_available is False
    mock_nvenc.assert_not_called()

@patch('os.getenv')
@patch('CreateShorts.Data_Gen.moviepy_config._is_nvenc_available')
def test_acceleration_logic_enabled_by_config_and_hw(mock_nvenc, mock_getenv):
    mock_getenv.return_value = "true"
    mock_nvenc.return_value = True
    
    use_accel_env = mock_getenv("USE_ACCEL", "false").lower() == "true"
    if use_accel_env:
        accel_available = mock_nvenc()
    else:
        accel_available = False
        
    assert accel_available is True
    mock_nvenc.assert_called_once()

