import json
import os
from CreateShorts.Models.script_models import ScriptDTO, SegmentDTO, HighlightDTO
from CreateShorts.Data_Gen.create_audio import assemble_dialogue_v2
from CreateShorts.theme_config import ThemeManager

def test_sfx_integration_v2():
    print("\n--- SFX Integration Test: Master Audio Assembly ---")
    
    # 1. Config paths
    mock_script_path = "CreateShorts/MockScriptFiles/sfx_test_script.json"
    mock_audio_path = "CreateShorts/MockAudioFiles/CreateShorts/resources/audio/temp_audio/mock_seg_0_Tina.mp3"
    output_audio = "output/sfx_master_test.mp3"
    
    # Ensure audio exists
    if not os.path.exists(mock_audio_path):
        print(f"❌ ERROR: Mock audio not found at {mock_audio_path}")
        return

    # 2. Load and parse the mock script
    with open(mock_script_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    segments = []
    for item in data:
        highlight = None
        if "highlight" in item:
            highlight = HighlightDTO(
                type=item["highlight"]["type"],
                context=item["highlight"]["context"]
            )
        
        segments.append(SegmentDTO(
            speaker=item["speaker"],
            line=item["line"],
            highlight=highlight,
            audio_path=mock_audio_path,
            duration=2.0  # Force a fixed duration for each mock segment
        ))

    script_dto = ScriptDTO(
        topic="SFX Integration Validation",
        segments=segments
    )

    # 3. Get default theme config
    tm = ThemeManager()
    theme_config = tm.get_theme_config("default")

    # 4. Run the assembly
    result = assemble_dialogue_v2(script_dto, theme_config, output_audio)
    
    if result and os.path.exists(output_audio):
        print(f"\n✅ SUCCESS: Master audio with SFX generated: {output_audio}")
        # Print expected times for manual validation
        print("Expected SFX hits (Triggered at END of each segment):")
        print("- Segment 1 (horror/jump_scare) -> Starts at 2.0s")
        print("- Segment 2 (comedy/laugh)      -> Starts at 4.0s")
        print("- Segment 3 (comedy/ba-dum-tss) -> Starts at 6.0s")
    else:
        print("\n❌ FAILURE: Audio assembly did not produce output.")

if __name__ == "__main__":
    test_sfx_integration_v2()
