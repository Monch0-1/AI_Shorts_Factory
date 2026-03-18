import logging
from CreateShorts.Services.SFXService import SFXService
from CreateShorts.theme_config import ThemeManager

# Configure logging to see the output
logging.basicConfig(level=logging.INFO)

def test_sfx_service_logic():
    print("\n--- Testing SFXService Logic ---")
    service = SFXService()
    
    # Test 1: Successful selection and DB update
    category = "horror"
    tag = "jump_scare"
    print(f"Testing selection for {category}/{tag}...")
    
    path1 = service.get_sfx_path(category, tag)
    if path1:
        print(f"✅ Success: Selected {path1}")
    else:
        print("❌ Failure: No SFX selected")

    # Test 2: Verify usage_count increment (manual check via path)
    # We'll just run it again to see if it works
    path2 = service.get_sfx_path(category, tag)
    if path2:
        print(f"✅ Success: Selected second time {path2}")

    # Test 3: Missing tag handling
    print("\nTesting missing tag handling...")
    path_missing = service.get_sfx_path("non_existent", "tag")
    if path_missing is None:
        print("✅ Success: Correctly handled missing tag with None")
    else:
        print(f"❌ Failure: Should have returned None but got {path_missing}")

    # Test 4: Sync Check
    print("\nTesting YAML to DB Sync...")
    theme_manager = ThemeManager()
    service.sync_yaml_to_db(theme_manager)

if __name__ == "__main__":
    test_sfx_service_logic()
