from dataclasses import dataclass
from typing import Optional

@dataclass
class VideoOptions:
    """Configuration options for the video generation process."""
    duration_seconds: int = 60
    video_index: Optional[int] = None
    enable_refiner: bool = False
    use_script_template: bool = False
    include_sfx: bool = True

@dataclass
class VideoRequest:
    """
    Encapsulates the parameters required to create a short video.
    Acts as a Data Transfer Object (DTO) for video generation requests.
    """
    topic: str
    theme: str = "default"
    is_monologue: bool = False
    context_story: str = ""
    options: VideoOptions = None

    def __post_init__(self):
        if self.options is None:
            self.options = VideoOptions()

    @classmethod
    def from_dict(cls, data: dict) -> 'VideoRequest':
        """Creates a VideoRequest instance from a dictionary, handling nested options."""
        # Extract options data if present
        options_data = data.get("options", {})
        
        # Mapping legacy or flat fields if they exist at the top level for backward compatibility
        duration = options_data.get("duration_seconds") if options_data.get("duration_seconds") is not None else data.get("duration_seconds", 60)
        v_index = options_data.get("video_index") if options_data.get("video_index") is not None else data.get("video_index")
        
        # Use explicit None check for booleans
        refiner = options_data.get("enable_refiner") if options_data.get("enable_refiner") is not None else data.get("enable_refiner", False)
        include_sfx = options_data.get("include_sfx") if options_data.get("include_sfx") is not None else data.get("include_sfx", True)
        
        # Handle rename from use_template to use_script_template
        template = options_data.get("use_script_template")
        if template is None:
            template = data.get("use_script_template")
        if template is None:
            template = data.get("use_template", False)

        options = VideoOptions(
            duration_seconds=duration,
            video_index=v_index,
            enable_refiner=refiner,
            use_script_template=template,
            include_sfx=include_sfx
        )

        return cls(
            topic=data.get("topic", "Untitled"),
            theme=data.get("theme", "default"),
            is_monologue=data.get("is_monologue") if data.get("is_monologue") is not None else False,
            context_story=data.get("context_story", ""),
            options=options
        )
