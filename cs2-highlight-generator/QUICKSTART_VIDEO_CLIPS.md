# Quick Start: From Demo File to Video Clips

## The Full Workflow

### Step 1: Upload Demo & Get Highlights

```bash
# Start the backend server
cd cs2-highlight-generator/backend
python main.py
```

Then upload your FaceIt demo via the frontend:
- Open `cs2-highlight-generator/frontend/index.html`
- Upload your `.dem` file
- Save the JSON response

### Step 2: Generate FFmpeg Script

**Option A: Via Frontend** (Coming soon - needs UI update)

**Option B: Via Command Line** (Works now!)

```bash
# Save your highlights to a file
cat > highlights.json << 'EOF'
{
  "highlights": [
    {
      "type": "ACE",
      "round": 3,
      "start_time": 145.2,
      "end_time": 163.8,
      "player": "YourName",
      "description": "YourName ACE with AK-47 in round 3"
    },
    {
      "type": "QUADRA_KILL",
      "round": 7,
      "start_time": 342.5,
      "end_time": 357.1,
      "player": "YourName",
      "description": "YourName 4K with Desert Eagle in round 7"
    }
  ]
}
EOF

# Generate the FFmpeg script
curl -X POST http://localhost:8000/api/export/ffmpeg-script \
  -H "Content-Type: application/json" \
  -d @highlights.json \
  > extract_highlights.sh

# Make it executable
chmod +x extract_highlights.sh
```

### Step 3: Extract Video Clips

```bash
# Run the script with your gameplay recording
./extract_highlights.sh path/to/your/gameplay_recording.mp4

# Clips will be created in highlight_clips/ directory
```

---

## Complete Example (All 3 Steps)

```bash
# 1. Analyze demo (via API)
curl -X POST http://localhost:8000/api/analyze \
  -F "demo_file=@my_faceit_match.dem" \
  > analysis_result.json

# 2. Extract just the highlights array
jq '.highlights' analysis_result.json > highlights.json

# 3. Generate FFmpeg script
curl -X POST http://localhost:8000/api/export/ffmpeg-script \
  -H "Content-Type: application/json" \
  -d @highlights.json \
  > extract_highlights.sh

# 4. Make executable
chmod +x extract_highlights.sh

# 5. Extract clips from your gameplay recording
./extract_highlights.sh ~/Videos/faceit_match_recording.mp4

# 6. Check the results
ls -lh highlight_clips/
# highlight_01_ACE_round3_YourName.mp4
# highlight_02_QUADRA_KILL_round7_YourName.mp4
# highlight_03_TRIPLE_KILL_round12_YourName.mp4
```

---

## Requirements

### For Video Extraction:

1. **FFmpeg installed:**
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

2. **Gameplay recording:**
   - You need a video file of your match
   - Record with OBS, ShadowPlay, or AMD ReLive
   - **Important:** Start recording BEFORE the match starts
   - Video timing must match demo timing

---

## How to Record Gameplay for This

### Option 1: Record While Playing (Best)

1. Install OBS Studio (free) or use ShadowPlay/ReLive
2. **Start recording BEFORE joining the match**
3. Play your match
4. Stop recording after match ends
5. You now have a video file synchronized with the demo

### Option 2: Record Demo Playback

If you didn't record while playing:

1. Open CS2
2. Start OBS recording
3. In console: `playdemo your_match.dem`
4. Let demo play (or use `demo_timescale 2` to speed up)
5. Stop recording when done

The video will be synchronized with demo timestamps!

---

## What If I Don't Have a Recording?

Three options:

### 1. Re-watch Demo with OBS (Easiest)
- Load demo in CS2
- Use OBS to record
- Jump to highlights: `demo_gototick <tick>`
- Record each one manually

### 2. Download from FACEIT (If available)
- Some FACEIT matches have VODs
- Check match room on FACEIT

### 3. Just Share Timestamps (No video)
- Post highlights JSON to Discord/Twitter
- Others can watch in-game using timestamps
- Example: "Check my ACE at tick 18560 (round 3)"

---

## Troubleshooting

### "Video timing doesn't match demo"

**Problem:** Clips show wrong parts of the match

**Solution:**
- Ensure you started recording BEFORE the match
- Demo timestamps start from match start, not from when you started recording
- Add offset to all timestamps if needed

### "FFmpeg not found"

**Problem:** Script says FFmpeg not installed

**Solution:**
```bash
# Check if installed
ffmpeg -version

# If not, install it
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Linux
```

### "Clips are cut off / too short"

**Problem:** Highlights end abruptly

**Solution:**
- Current padding: 5 seconds before, 3 seconds after
- Adjust in `config.py` (search for "padding")
- Regenerate highlights with new settings

---

## Next Steps

Want to combine clips into a montage?

```bash
# List all clips
ls highlight_clips/*.mp4 > clips.txt

# Create montage with FFmpeg
ffmpeg -f concat -safe 0 -i clips.txt \
       -c copy \
       highlights_montage.mp4
```

Add music, transitions, effects with:
- DaVinci Resolve (free)
- Adobe Premiere Pro
- Final Cut Pro
- Shotcut (free, open source)

---

## API Reference

### POST /api/export/ffmpeg-script

**Request:**
```json
[
  {
    "type": "ACE",
    "round": 3,
    "start_time": 145.2,
    "end_time": 163.8,
    "player": "YourName",
    "description": "YourName ACE with AK-47 in round 3"
  }
]
```

**Response:**
```bash
#!/bin/bash
# CS2 Highlight Extractor - Auto-generated FFmpeg script
# ... (executable bash script)
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/export/ffmpeg-script \
     -H "Content-Type: application/json" \
     -d '[{"type":"ACE","start_time":145.2,"end_time":163.8,...}]' \
     > extract.sh
chmod +x extract.sh
./extract.sh my_video.mp4
```

---

## Summary

**You asked:** "how we would end up with a short video of a particular highlight?"

**Answer:**

1. ✅ Upload `.dem` file → Get highlights JSON (what you have now)
2. ✅ POST highlights to `/api/export/ffmpeg-script` → Get bash script (NEW!)
3. ✅ Run script with your gameplay recording → Get video clips! (NEW!)

The app now has the capability to generate video clips - you just need a gameplay recording to cut from!

For full automation (rendering from .dem without recording), see `HOW_TO_GET_VIDEOS.md` - it's more complex and requires manual steps.
