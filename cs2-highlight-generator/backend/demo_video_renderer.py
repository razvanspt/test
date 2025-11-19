"""
Demo Video Renderer
Renders CS2 demo files directly to video using CS2's built-in demo player

This is the BETTER approach - no need for separate gameplay recording!

Methods:
1. Use CS2 console commands to play demo and record
2. Automate with startmovie command (Source engine feature)
3. Use third-party tools like HLAE (Half-Life Advanced Effects)
"""

import logging
import subprocess
import platform
import time
from pathlib import Path
from typing import List, Optional

from models import HighlightMoment

logger = logging.getLogger(__name__)


class DemoVideoRenderer:
    """
    Render CS2 demos directly to video

    This uses CS2's built-in demo player to render highlights
    without needing a separate gameplay recording.
    """

    def __init__(self, cs2_install_path: Optional[Path] = None):
        """
        Initialize renderer

        Args:
            cs2_install_path: Path to CS2 installation
                             (e.g., "C:/Program Files (x86)/Steam/steamapps/common/Counter-Strike Global Offensive")
        """
        self.cs2_path = cs2_install_path or self._find_cs2_installation()
        self.system = platform.system()

        if self.cs2_path:
            logger.info(f"CS2 installation found: {self.cs2_path}")
        else:
            logger.warning("CS2 installation not found. Demo rendering will not work.")

    def _find_cs2_installation(self) -> Optional[Path]:
        """Try to auto-detect CS2 installation"""

        if self.system == "Windows":
            # Common Steam installation paths on Windows
            possible_paths = [
                Path("C:/Program Files (x86)/Steam/steamapps/common/Counter-Strike Global Offensive"),
                Path("D:/Steam/steamapps/common/Counter-Strike Global Offensive"),
                Path("E:/Steam/steamapps/common/Counter-Strike Global Offensive"),
            ]
        elif self.system == "Linux":
            # Linux Steam path
            home = Path.home()
            possible_paths = [
                home / ".steam/steam/steamapps/common/Counter-Strike Global Offensive",
                home / ".local/share/Steam/steamapps/common/Counter-Strike Global Offensive",
            ]
        elif self.system == "Darwin":  # macOS
            possible_paths = [
                Path.home() / "Library/Application Support/Steam/steamapps/common/Counter-Strike Global Offensive",
            ]
        else:
            return None

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def generate_demo_playback_script(
        self,
        demo_file: Path,
        highlight: HighlightMoment,
        output_video: Path
    ) -> str:
        """
        Generate CS2 console commands to play demo and record highlight

        CS2 Source Engine Commands:
        - playdemo <demo>: Play a demo file
        - demo_gototick <tick>: Jump to specific tick
        - demo_pause: Pause demo
        - demo_resume: Resume demo
        - startmovie <filename>: Start recording frames to TGA/WAV
        - endmovie: Stop recording

        Returns:
            CFG file content with console commands
        """
        # Calculate ticks (CS2 runs at 128 tick)
        start_tick = highlight.start_tick
        end_tick = highlight.end_tick

        # Generate CFG commands
        cfg = f"""// Auto-generated highlight recording script
// Highlight: {highlight.description}
// Round: {highlight.round_number}

// Load demo
playdemo "{demo_file.name}"

// Jump to highlight start (minus buffer)
demo_gototick {start_tick}

// Wait for demo to load
wait 60

// Start recording
// Note: This will create TGA frames in csgo/ directory
// You'll need to combine them with FFmpeg afterwards
startmovie "{output_video.stem}" fps 60

// Fast forward to end tick
demo_gototick {end_tick}

// Wait for recording
wait 30

// Stop recording
endmovie

// Exit CS2
quit
"""
        return cfg

    def render_highlight_to_frames(
        self,
        demo_file: Path,
        highlight: HighlightMoment,
        output_dir: Path,
        index: int = 1
    ) -> Path:
        """
        Render a highlight to video frames using CS2

        This launches CS2, plays the demo, and uses 'startmovie' to record frames.

        Args:
            demo_file: Path to .dem file
            highlight: Highlight to render
            output_dir: Where to save frames
            index: Highlight index for naming

        Returns:
            Path to CFG file (user must run CS2 with this CFG manually)

        Note:
            This method generates a CFG file that the user must execute in CS2.
            Fully automated rendering requires more complex setup (HLAE, etc.)
        """
        if not self.cs2_path:
            raise Exception("CS2 installation not found")

        # Create output directory
        frames_dir = output_dir / f"highlight_{index:02d}_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        # Generate CFG file
        output_name = f"highlight_{index:02d}_{highlight.type}_round{highlight.round_number}"
        cfg_content = self.generate_demo_playback_script(demo_file, highlight, frames_dir / output_name)

        # Save CFG to CS2 cfg directory
        cs2_cfg_dir = self.cs2_path / "game" / "csgo" / "cfg"
        cfg_file = cs2_cfg_dir / f"record_highlight_{index}.cfg"

        try:
            cfg_file.write_text(cfg_content)
            logger.info(f"✓ Generated CS2 config: {cfg_file}")

            # Create instructions file
            instructions = f"""CS2 Demo Highlight Recording Instructions
=============================================

Highlight: {highlight.description}
Round: {highlight.round_number}
Duration: {highlight.end_time - highlight.start_time:.1f} seconds

HOW TO RECORD THIS HIGHLIGHT:
==============================

1. Copy the demo file to CS2:
   Copy: {demo_file}
   To:   {self.cs2_path / 'game' / 'csgo'}

2. Launch CS2

3. Open console (press ~) and type:
   exec record_highlight_{index}.cfg

4. CS2 will automatically:
   - Load the demo
   - Jump to the highlight
   - Record frames (TGA images + WAV audio)
   - Exit when done

5. Find the frames in:
   {self.cs2_path / 'game' / 'csgo'}
   (Look for files starting with '{output_name}')

6. Convert frames to video with FFmpeg:
   ffmpeg -framerate 60 -i {output_name}%04d.tga -i {output_name}.wav \\
          -c:v libx264 -preset slow -crf 18 -c:a aac \\
          {output_name}.mp4

NOTES:
======
- This will create MANY large TGA files (~30MB each)
- Expect 10-20GB for a 30-second clip
- Make sure you have enough disk space!
- You can change FPS in the CFG file (default: 60)

ALTERNATIVE (Easier):
=====================
If you recorded your gameplay with OBS/ShadowPlay,
use video_clip_generator.py instead!
"""

            instructions_file = output_dir / f"highlight_{index:02d}_instructions.txt"
            instructions_file.write_text(instructions)

            logger.info(f"✓ Created instructions: {instructions_file}")
            logger.info("⚠️  User must manually execute CFG in CS2 to render")

            return cfg_file

        except Exception as e:
            logger.error(f"Failed to create CS2 config: {e}")
            raise

    def generate_batch_script(
        self,
        demo_file: Path,
        highlights: List[HighlightMoment],
        output_dir: Path
    ) -> Path:
        """
        Generate a script to render all highlights

        Returns:
            Path to instructions file
        """
        instructions = f"""CS2 Demo Highlight Rendering - BATCH MODE
==========================================

Demo File: {demo_file.name}
Total Highlights: {len(highlights)}

AUTOMATED WORKFLOW (Recommended):
==================================

Unfortunately, CS2 doesn't support fully automated demo rendering from command line.
You have TWO options:

OPTION 1: Use Recorded Gameplay (EASIEST)
------------------------------------------
If you recorded your gameplay with OBS, ShadowPlay, or GeForce Experience:

1. Put your gameplay video in: {output_dir}
2. Run: python main.py --extract-clips <your_video.mp4>

This will automatically cut your video at the highlight timestamps!


OPTION 2: Manual Rendering in CS2 (HIGH QUALITY)
-------------------------------------------------
Render highlights directly from demo for perfect quality:

"""

        for i, h in enumerate(highlights, 1):
            instructions += f"\nHighlight {i}: {h.description}\n"
            instructions += f"  Round: {h.round_number}\n"
            instructions += f"  Player: {h.player_name}\n"
            instructions += f"  Time: {h.start_time:.1f}s - {h.end_time:.1f}s\n"
            instructions += f"  Command: exec record_highlight_{i}.cfg\n"

        instructions += f"""

MANUAL STEPS FOR EACH HIGHLIGHT:
1. Launch CS2
2. Open console (~)
3. Type: exec record_highlight_<number>.cfg
4. Wait for CS2 to record and exit
5. Combine frames with FFmpeg (see individual instruction files)
6. Repeat for next highlight


RECOMMENDED: Option 1 is MUCH easier!
======================================
Unless you need perfect quality or slow-motion effects,
use Option 1 with your gameplay recording.

"""

        instructions_file = output_dir / "RENDERING_INSTRUCTIONS.txt"
        instructions_file.write_text(instructions)

        logger.info(f"✓ Created batch instructions: {instructions_file}")
        return instructions_file


class SimpleVideoWorkflow:
    """
    Simplified workflow recommendation for users
    """

    @staticmethod
    def get_recommendation() -> str:
        return """
╔══════════════════════════════════════════════════════════════╗
║  HOW TO GET VIDEO CLIPS FROM YOUR HIGHLIGHTS                ║
╚══════════════════════════════════════════════════════════════╝

You have 3 OPTIONS (ranked by ease):

📹 OPTION 1: Upload Recorded Gameplay (EASIEST) ✅
───────────────────────────────────────────────────
If you recorded your match with OBS/ShadowPlay:

1. Upload your .dem file (you already did this!)
2. Upload your gameplay video file
3. We'll automatically cut clips at highlight timestamps
4. Done! Download your clips

Pros: Super easy, fully automated
Cons: Need to have recorded gameplay

─────────────────────────────────────────────────────

🎮 OPTION 2: Re-watch Demo in CS2 + OBS (EASY)
───────────────────────────────────────────────────
1. Open CS2
2. Start OBS recording
3. Load demo: playdemo <filename>
4. Use demo_gototick <tick> to jump to highlights
5. Record each highlight
6. Edit in video editor

Pros: Good quality, flexible
Cons: Manual work, need to jump to each timestamp

─────────────────────────────────────────────────────

⚙️  OPTION 3: CS2 'startmovie' Command (HARD)
───────────────────────────────────────────────────
Use CS2's built-in frame renderer:

1. Create CFG file with commands
2. Launch CS2 with CFG
3. CS2 renders frames (TGA format)
4. Combine frames with FFmpeg
5. Cleanup huge TGA files

Pros: Highest quality, can do slow-motion
Cons: Very manual, requires disk space (10-20GB per clip!)

─────────────────────────────────────────────────────

💡 RECOMMENDATION: Use Option 1 or 2

For most users, Option 1 (upload gameplay video) is best.
For highlights without recording, use Option 2 (re-watch + OBS).

═══════════════════════════════════════════════════════
"""
