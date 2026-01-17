import glob
from moviepy.config import change_settings

# Configure ImageMagick

# Attempt to find ImageMagick dynamically to handle version updates
possible_paths = glob.glob(r"C:\Program Files\ImageMagick*\magick.exe")
if possible_paths:
    IMAGEMAGICK_PATH = sorted(possible_paths)[-1]
else:
    IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"

change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})
