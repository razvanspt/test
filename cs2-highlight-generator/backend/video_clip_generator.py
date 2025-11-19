"""
Video Clip Generator
Generates actual video clips from recorded gameplay using FFmpeg

This requires:
1. A .dem demo file (for highlight timestamps)
2. A recorded video file of the match (from OBS, ShadowPlay, etc.)
"""

import logging
import subprocess
from pathlib import Path
from typing import List
import shutil

from models import HighlightMoment

logger = logging.getLogger(__name__)


class VideoClipGenerator:
    """
    Generate video clips from highlights using FFmpeg

    Workflow:
    1. User uploads .dem file -> we detect highlights
    2. User uploads their gameplay video
    3. We use FFmpeg to cut clips at highlight timestamps
    """

    def __init__(self):
        """Check if FFmpeg is available"""
        self.ffmpeg_available = shutil.which("ffmpeg") is not None
        if not self.ffmpeg_available:
            logger.warning("FFmpeg not found! Video generation will not work.")
            logger.warning("Install: sudo apt install ffmpeg (Linux) or brew install ffmpeg (Mac)")
        else:
            logger.info("FFmpeg found - video generation available")

    def generate_clip(
        self,
        input_video: Path,
        highlight: HighlightMoment,
        output_dir: Path,
        clip_index: int = 1
    ) -> Path:
        """
        Generate a single highlight clip

        Args:
            input_video: Path to full gameplay video
            highlight: Highlight moment with timestamps
            output_dir: Directory to save clips
            clip_index: Index number for filename

        Returns:
            Path to generated clip

        Raises:
            Exception: If FFmpeg fails
        """
        if not self.ffmpeg_available:
            raise Exception("FFmpeg is not installed. Cannot generate video clips.")

        if not input_video.exists():
            raise FileNotFoundError(f"Input video not found: {input_video}")

        # Create output filename
        output_file = output_dir / f"highlight_{clip_index:02d}_{highlight.type}_round{highlight.round_number}_{highlight.player_name}.mp4"

        # FFmpeg command
        # -ss: start time (before input for fast seeking)
        # -i: input file
        # -t: duration
        # -c:v libx264: re-encode video (for compatibility)
        # -c:a aac: re-encode audio
        # -preset fast: encoding speed
        # -crf 18: quality (lower = better, 18 = visually lossless)

        start_time = highlight.start_time
        duration = highlight.end_time - highlight.start_time

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-ss", str(start_time),  # Seek to start time
            "-i", str(input_video),
            "-t", str(duration),  # Duration
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            "-crf", "18",
            str(output_file)
        ]

        logger.info(f"Generating clip {clip_index}: {highlight.description}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr}")

            if not output_file.exists():
                raise Exception("Output file was not created")

            file_size_mb = output_file.stat().st_size / 1024 / 1024
            logger.info(f"✓ Generated clip: {output_file.name} ({file_size_mb:.1f} MB)")

            return output_file

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timed out after 5 minutes")
            raise Exception("Video generation timed out")

    def generate_all_clips(
        self,
        input_video: Path,
        highlights: List[HighlightMoment],
        output_dir: Path
    ) -> List[Path]:
        """
        Generate clips for all highlights

        Args:
            input_video: Path to full gameplay video
            highlights: List of highlights
            output_dir: Directory to save clips

        Returns:
            List of paths to generated clips
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_clips = []

        for i, highlight in enumerate(highlights, 1):
            try:
                clip_path = self.generate_clip(input_video, highlight, output_dir, i)
                generated_clips.append(clip_path)
            except Exception as e:
                logger.error(f"Failed to generate clip {i}: {e}")
                continue

        logger.info(f"✓ Generated {len(generated_clips)}/{len(highlights)} clips")
        return generated_clips

    def generate_ffmpeg_script(
        self,
        highlights: List[HighlightMoment],
        output_path: Path
    ) -> Path:
        """
        Generate a bash script with FFmpeg commands

        This is useful if user wants to manually run the commands

        Args:
            highlights: List of highlights
            output_path: Path to save the script

        Returns:
            Path to generated script
        """
        script = "#!/bin/bash\n"
        script += "# FFmpeg script to extract CS2 highlights\n"
        script += "# Usage: ./extract_highlights.sh your_gameplay_recording.mp4\n"
        script += "#\n"
        script += "# Requirements:\n"
        script += "# - FFmpeg installed\n"
        script += "# - Gameplay video file\n"
        script += "#\n"
        script += "# Note: Demo timestamps and video timestamps must be synchronized!\n"
        script += "#       Start recording BEFORE starting the demo/match.\n\n"

        script += 'if [ -z "$1" ]; then\n'
        script += '    echo "Error: No input video specified"\n'
        script += '    echo "Usage: $0 your_gameplay_recording.mp4"\n'
        script += '    exit 1\n'
        script += 'fi\n\n'

        script += 'INPUT_VIDEO="$1"\n'
        script += 'OUTPUT_DIR="highlight_clips"\n'
        script += 'mkdir -p "$OUTPUT_DIR"\n\n'

        for i, h in enumerate(highlights, 1):
            start = h.start_time
            duration = h.end_time - h.start_time

            output_file = f"highlight_{i:02d}_{h.type}_round{h.round_number}_{h.player_name}.mp4"

            script += f"# Clip {i}: {h.description}\n"
            script += f"echo 'Generating clip {i}/{len(highlights)}: {h.description}'\n"
            script += f'ffmpeg -y -ss {start} -i "$INPUT_VIDEO" -t {duration} '
            script += f'-c:v libx264 -c:a aac -preset fast -crf 18 '
            script += f'"$OUTPUT_DIR/{output_file}"\n\n'

        script += f'echo "✓ Generated {len(highlights)} highlight clips in $OUTPUT_DIR/"\n'

        # Write script
        output_path.write_text(script)
        output_path.chmod(0o755)  # Make executable

        logger.info(f"✓ Generated FFmpeg script: {output_path}")
        return output_path
