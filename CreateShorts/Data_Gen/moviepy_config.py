import glob
import os
import platform
import subprocess
from moviepy.config import change_settings, get_setting

# Configure ImageMagick
if platform.system() == "Windows":
    # Attempt to find ImageMagick dynamically to handle version updates
    possible_paths = glob.glob(r"C:\Program Files\ImageMagick*\magick.exe")
    if possible_paths:
        IMAGEMAGICK_PATH = sorted(possible_paths)[-1]
    else:
        IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
else:
    # Linux / Docker configuration
    if os.path.exists("/usr/bin/magick"):
        IMAGEMAGICK_PATH = "/usr/bin/magick"
    else:
        IMAGEMAGICK_PATH = r"/usr/bin/convert"

change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

def _is_nvenc_available():
    """
    Validates if NVENC is actually usable by running a probe.
    This ensures that the GPU, drivers, and FFmpeg binary are all working together.
    """
    ffmpeg_bin = get_setting("FFMPEG_BINARY")
    if not ffmpeg_bin:
        return False

    try:
        # Attempt to initialize the encoder with a null input
        # We use 1920x1080 because some NVENC versions fail with tiny dimensions
        cmd = [ffmpeg_bin, "-y", "-f", "lavfi", "-i", "nullsrc=s=1920x1080:d=0.1", "-c:v", "h264_nvenc", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

# Detect acceleration at module load time (Singleton-like behavior)
# Priority 1: Configuration (.env)
USE_ACCEL_ENV = os.getenv("USE_ACCEL", "false").lower() == "true"

# Priority 2: Physical hardware availability (only if enabled by config)
if USE_ACCEL_ENV:
    ACCELERATION_AVAILABLE = _is_nvenc_available()
else:
    ACCELERATION_AVAILABLE = False

print("\n" + "="*60)
if ACCELERATION_AVAILABLE:
    print("⚡ HARDWARE ACCELERATION: NVIDIA NVENC ENABLED")
    print("📊 STATUS: GPU Rendering will be used for all video tasks.")
    print("🎯 ENCODER: h264_nvenc (NVIDIA RTX 5080/Compatible)")
elif USE_ACCEL_ENV and not ACCELERATION_AVAILABLE:
    print("⚠️  HARDWARE ACCELERATION: ENABLED BY CONFIG BUT HARDWARE NOT FOUND")
    print("📊 STATUS: Falling back to CPU-based rendering (libx264).")
else:
    print("💻 HARDWARE ACCELERATION: DISABLED BY CONFIGURATION")
    print("📊 STATUS: Using CPU-based rendering (libx264).")
    print("⚠️  NOTE: Rendering times will be significantly longer.")
print("="*60 + "\n")

def get_render_params():
    """
    Returns optimized parameters for write_videofile based on detected hardware.
    Used for centralized configuration of output quality and speed.
    """
    if ACCELERATION_AVAILABLE:
        return {
            "codec": "h264_nvenc",
            "ffmpeg_params": [
                "-preset", "p3",    # Slightly lower preset for broader compatibility
                "-tune", "hq",      # High quality tuning
                "-b:v", "5M",       # Target bitrate for 1080p
                "-maxrate", "8M",
                "-bufsize", "10M",
                "-pix_fmt", "yuv420p", # Force standard pixel format
                "-movflags", "+faststart" # Optimize for web/streaming
            ]
        }
    else:
        return {
            "codec": "libx264",
            "ffmpeg_params": [
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart"
            ]
        }

