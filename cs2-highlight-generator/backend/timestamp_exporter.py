"""
Timestamp Exporter Utility
Exports highlight timestamps in various formats for video editing

This can be used to generate timestamp files for:
- FFmpeg (for automated video cutting)
- YouTube chapters
- Video editing software
"""

from typing import List
from models import HighlightMoment
import json


class TimestampExporter:
    """
    Utility class for exporting timestamps

    In Java:
    public class TimestampExporter {
        public String exportAsFFmpegScript(List<HighlightMoment> highlights) { ... }
    }
    """

    @staticmethod
    def export_as_json(highlights: List[HighlightMoment]) -> str:
        """
        Export highlights as JSON

        Args:
            highlights: List of highlight moments

        Returns:
            JSON string
        """
        data = []
        for h in highlights:
            data.append({
                "type": h.type,
                "round": h.round_number,
                "start_time": h.start_time,
                "end_time": h.end_time,
                "duration": h.end_time - h.start_time,
                "player": h.player_name,
                "description": h.description
            })
        return json.dumps(data, indent=2)

    @staticmethod
    def export_as_ffmpeg_script(highlights: List[HighlightMoment]) -> str:
        """
        Export as FFmpeg commands for cutting video

        Assumes you have a recorded gameplay video file

        Returns:
            Bash script with FFmpeg commands
        """
        script = "#!/bin/bash\n"
        script += "# FFmpeg script to extract highlights\n"
        script += "# Usage: ./extract_highlights.sh input_video.mp4\n\n"
        script += "INPUT_VIDEO=$1\n\n"

        for i, h in enumerate(highlights, 1):
            start = h.start_time
            duration = h.end_time - h.start_time

            # FFmpeg command to extract clip
            # -ss: start time
            # -t: duration
            # -c copy: copy without re-encoding (fast)
            output_file = f"highlight_{i}_{h.type}_{h.round_number}.mp4"

            script += f"# Highlight {i}: {h.description}\n"
            script += f"ffmpeg -i \"$INPUT_VIDEO\" -ss {start} -t {duration} -c copy \"{output_file}\"\n\n"

        return script

    @staticmethod
    def export_as_youtube_chapters(highlights: List[HighlightMoment]) -> str:
        """
        Export as YouTube chapters format

        Returns:
            Text in YouTube chapter format (HH:MM:SS - Description)
        """
        chapters = "0:00 - Match Start\n"

        for h in highlights:
            # Convert seconds to HH:MM:SS
            minutes = int(h.start_time // 60)
            seconds = int(h.start_time % 60)
            timestamp = f"{minutes}:{seconds:02d}"

            chapters += f"{timestamp} - {h.description}\n"

        return chapters
