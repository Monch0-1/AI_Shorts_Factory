# AI Short-Video Generator (WIP)

An automated pipeline designed to transform a simple idea or topic into a fully rendered short-form video. By leveraging **Google Gemini** for scriptwriting and **ElevenLabs** for high-quality narration, this tool automates the tedious parts of content creation.

## 🚀 Overview
This project aims to bridge the gap between a concept and a final video. Users provide a topic or story context, and the system handles the heavy lifting:
1. **Script Generation:** Crafting a narrative via Google Gemini.
2. **Voice Synthesis:** Converting text to speech using ElevenLabs.
3. **Video Assembly:** Combining audio, templates, and assets using MoviePy.

## 🛠️ Configuration & Parameters
The script processes a data dictionary to define the video's attributes. You can customize the output using the following parameters:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `topic` | String | "Untitled" | The main subject of the video. |
| `duration_seconds` | Integer | 60 | Target length for the final output. |
| `theme` | String | "default" | Visual style or aesthetic profile. |
| `use_template` | Boolean | False | Whether to use a pre-defined layout. |
| `is_monologue` | Boolean | False | Toggles between single-voice or multi-voice scripts. |
| `context_story` | String | "" | Additional background info to guide the AI. |

### Usage Example
```python
# The script processes a configuration dictionary like this:
data = {
    "topic": "The Future of Mars Colonization",
    "duration_seconds": 30,
    "theme": "cinematic",
    "is_monologue": True,
    "context_story": "Focus on the first 100 days of the colony."
}
```

### Project Roadmap (WIP)
[ ] Core Pipeline: Connect the standalone video generation engine (currently using local templates).

[ ] API Layer: Develop a REST API to enable web-based triggers.

[ ] Integrations: Add a WhatsApp bot interface for "on-the-go" video requests.

[ ] Infrastructure: Complete the Dockerfile and Compose setup for easy deployment.

[ ] Documentation: Comprehensive API docs and setup guides.

### Requirements
- Ensure you have the following dependencies installed:
- moviepy
- google-genai
- google-api-python-client
- python-dotenv
- pydub
- pyyaml
- ElevenLabs

### Setup
- Clone the repository.
- Create a .env file in the root directory.
- Add your API keys:
  
```dptenv
GOOGLE_API_KEY=your_google_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```
- Run the main script to generate your first video.
  


