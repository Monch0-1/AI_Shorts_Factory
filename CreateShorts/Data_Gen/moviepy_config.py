import glob
import os
import platform
from moviepy.config import change_settings

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
        IMAGEMAGICK_PATH = "/usr/bin/convert"

change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
