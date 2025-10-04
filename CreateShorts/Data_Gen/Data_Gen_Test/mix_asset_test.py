"""
Unit tests for the mix_assets module
"""

import os
import tempfile
import unittest

import numpy as np
from moviepy.editor import AudioFileClip, VideoFileClip, ColorClip

from CreateShorts.Data_Gen.mix_assets import (
    create_mixed_audio_clip,
    format_video_vertical,
    create_final_video,
    VideoMixingError,
    VERTICAL_WIDTH,
    VERTICAL_HEIGHT
)


class TestMixAssets(unittest.TestCase):
    """Test suite for mix_assets module"""

    @classmethod
    def setUpClass(cls):
        """Create temporary test files and directories"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.create_test_files()

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary files and directories"""
        for file in os.listdir(cls.temp_dir):
            os.remove(os.path.join(cls.temp_dir, file))
        os.rmdir(cls.temp_dir)

    @classmethod
    def create_test_files(cls):
        """Create test audio and video files"""
        # Create test audio files
        duration = 2.0  # 2 seconds
        fps = 44100
        t = np.linspace(0, duration, int(fps * duration))

        # Voice audio (440 Hz tone)
        voice_audio = np.sin(2 * np.pi * 440 * t)
        cls.voice_path = os.path.join(cls.temp_dir, "test_voice.mp3")
        AudioFileClip(lambda s: voice_audio[int(s * fps)]).write_audiofile(cls.voice_path)

        # Background music (880 Hz tone)
        music_audio = np.sin(2 * np.pi * 880 * t)
        cls.music_path = os.path.join(cls.temp_dir, "test_music.mp3")
        AudioFileClip(lambda s: music_audio[int(s * fps)]).write_audiofile(cls.music_path)

        # Create test video file (red rectangle)
        cls.video_path = os.path.join(cls.temp_dir, "test_video.mp4")
        video = ColorClip(size=(640, 480), color=(255, 0, 0), duration=duration)
        video.write_videofile(cls.video_path, fps=30)

        # Output path for final video
        cls.output_path = os.path.join(cls.temp_dir, "output_video.mp4")

    def test_create_mixed_audio_clip(self):
        """Test audio mixing functionality"""
        duration = 2.0
        mixed_audio = create_mixed_audio_clip(self.voice_path, self.music_path, duration)

        self.assertIsNotNone(mixed_audio)
        self.assertEqual(mixed_audio.duration, duration)
        mixed_audio.close()

    def test_format_video_vertical(self):
        """Test video formatting to vertical aspect ratio"""
        duration = 2.0
        video_clip = VideoFileClip(self.video_path)
        formatted_video = format_video_vertical(video_clip, duration)

        self.assertEqual(formatted_video.size, (VERTICAL_WIDTH, VERTICAL_HEIGHT))
        self.assertEqual(formatted_video.duration, duration)

        video_clip.close()
        formatted_video.close()

    def test_create_final_video(self):
        """Test complete video creation process"""
        duration = 2.0
        create_final_video(
            self.voice_path,
            self.music_path,
            self.video_path,
            self.output_path,
            duration
        )

        self.assertTrue(os.path.exists(self.output_path))

        # Verify output video properties
        output_video = VideoFileClip(self.output_path)
        self.assertEqual(output_video.size, (VERTICAL_WIDTH, VERTICAL_HEIGHT))
        self.assertEqual(output_video.duration, duration)
        output_video.close()

    def test_invalid_audio_path(self):
        """Test error handling for invalid audio file path"""
        with self.assertRaises(VideoMixingError):
            create_mixed_audio_clip(
                "nonexistent_voice.mp3",
                self.music_path,
                2.0
            )

    def test_invalid_video_path(self):
        """Test error handling for invalid video file path"""
        with self.assertRaises(VideoMixingError):
            create_final_video(
                self.voice_path,
                self.music_path,
                "nonexistent_video.mp4",
                self.output_path,
                2.0
            )

    def test_invalid_duration(self):
        """Test error handling for invalid duration"""
        with self.assertRaises(VideoMixingError):
            create_final_video(
                self.voice_path,
                self.music_path,
                self.video_path,
                self.output_path,
                -1.0  # Negative duration
            )


if __name__ == '__main__':
    unittest.main()