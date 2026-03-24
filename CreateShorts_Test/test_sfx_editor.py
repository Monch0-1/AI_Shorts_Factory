import sys
import os
import time
from pathlib import Path

# Add project root to sys.path to ensure imports work correctly
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from Create_New_Short import create_short_from_json
from CreateShorts.Models.video_models import VideoRequest, VideoOptions

def test_professional_sfx_editor_pipeline():
    """
    Test the full pipeline with the new Professional SFX Editor logic.
    This test verifies that the system can handle the new sfx timing and volume fields.
    """
    start_time = time.time()

    # Testing the new Professional SFX Editor logic
    video_options = VideoOptions(
        duration_seconds=30, 
        video_index=None,
        enable_refiner=False, 
        use_script_template=False,
        include_sfx=True 
    )

    video_request = VideoRequest(
        topic="A robot trying to paint like Van Gogh but only making a mess",
        theme="default", 
        is_monologue=True, 
        context_story="The robot is named ArtBot 5000 and it's very enthusiastic.",
        options=video_options
    )

    print("\n🚀 Starting Test: Professional SFX Editor Mode...")
    # This will actually run the pipeline and generate a video in output/
    create_short_from_json(video_request)

    end_time = time.time()
    print(f"\n⏱️ Pipeline execution completed in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    test_professional_sfx_editor_pipeline()
