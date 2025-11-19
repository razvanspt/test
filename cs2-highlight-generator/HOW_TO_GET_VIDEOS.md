# How to Get Video Clips from Your Highlights

## Current State

The app currently provides **JSON timestamps** for highlights, not actual video files.

When you upload a `.dem` file, you get:
```json
{
  "highlights": [
    {
      "type": "ACE",
      "round": 3,
      "start_time": 145.2,
      "end_time": 163.8,
      "player": "YourName",
      "description": "YourName ACE with AK-47 in round 3"
    }
  ]
}
```

## How to Turn Timestamps into Videos

### ✅ OPTION 1: Upload Gameplay Recording (Easiest!)

If you recorded your match with OBS, ShadowPlay, or GeForce Experience:

```bash
# 1. Get FFmpeg script for your highlights
curl -X POST http://localhost:8000/api/export/ffmpeg \
  -H "Content-Type: application/json" \
  -d '{"highlights": [...your highlights...]}'

# 2. Run the script with your gameplay video
./extract_highlights.sh your_gameplay_video.mp4

# 3. Done! Clips are in highlight_clips/ directory
```

**Pros:**
- Fully automated
- Fast (just cuts existing video)
- Good quality

**Cons:**
- Need to have recorded gameplay
- Need to match demo timing to video timing

---

### ✅ OPTION 2: Re-watch Demo + OBS (Easy)

1. Open CS2
2. Start OBS recording
3. Open console and load demo:
   ```
   playdemo your_demo_file.dem
   ```
4. Jump to each highlight timestamp:
   ```
   demo_gototick 18560    # Jump to tick 18560 (145.2 seconds)
   demo_pause              # Pause
   demo_resume             # Resume recording
   ```
5. Record each highlight manually
6. Edit clips in video editor

**Pros:**
- Works without prior recording
- Full control
- Can add effects

**Cons:**
- Manual work for each highlight
- Time consuming

---

### ⚙️ OPTION 3: CS2 'startmovie' (Advanced)

Use CS2's built-in frame renderer:

```
// In CS2 console:
playdemo your_demo.dem
demo_gototick 18560
startmovie highlight_01 fps 60
demo_gototick 23526
endmovie
```

Then combine frames with FFmpeg:
```bash
ffmpeg -framerate 60 -i highlight_01%04d.tga -i highlight_01.wav \
       -c:v libx264 -crf 18 -c:a aac \
       highlight_01.mp4
```

**Pros:**
- Highest quality
- Can render slow-motion
- No recording needed

**Cons:**
- Very manual
- Creates HUGE TGA files (10-20GB per 30sec clip!)
- Need to run FFmpeg for each clip

---

## Recommended Workflow

### For Casual Use:
1. Record your gameplay with OBS/ShadowPlay while playing
2. Upload .dem to our app → get timestamps
3. Use Option 1 to auto-cut your recording

### For Highlight Reels:
1. Upload .dem → get timestamps
2. Use Option 2 to record highlights in CS2 with OBS
3. Edit clips together with music/effects

### For Pro Quality:
1. Use Option 3 with startmovie
2. Render at high FPS (300+) for slow-motion
3. Professional editing

---

## Future Feature: Automatic Video Generation

**Coming Soon:** Upload .dem file → get video clips automatically!

This would require:
- Server-side CS2 installation
- Headless demo rendering
- FFmpeg post-processing
- Large storage for frames

Currently investigating:
- HLAE (Half-Life Advanced Effects)
- Source engine headless mode
- Cloud rendering services

---

## Example: Full Workflow with Option 1

```bash
# 1. Upload demo and get highlights
curl -X POST http://localhost:8000/api/analyze \
  -F "demo_file=@my_match.dem" \
  > highlights.json

# 2. Generate FFmpeg script
curl -X POST http://localhost:8000/api/export/ffmpeg \
  -H "Content-Type: application/json" \
  -d @highlights.json \
  > extract_highlights.sh

# 3. Make it executable
chmod +x extract_highlights.sh

# 4. Run with your gameplay video
./extract_highlights.sh my_gameplay_recording.mp4

# 5. Clips are ready!
ls highlight_clips/
# highlight_01_ACE_round3_YourName.mp4
# highlight_02_QUADRA_KILL_round7_YourName.mp4
# highlight_03_TRIPLE_KILL_round12_YourName.mp4
```

---

## Why Not Fully Automated?

CS2 doesn't support headless demo rendering out of the box. Challenges:

1. **No CLI rendering** - CS2 requires GUI interaction
2. **File sizes** - TGA frames are 10-20GB per 30sec clip
3. **Server resources** - Would need GPU for rendering
4. **Licensing** - Running CS2 server-side may violate ToS

For now, **Option 1** (upload recording) is the best balance of automation and practicality.

---

## Questions?

- How do I record gameplay? → Use OBS, ShadowPlay, or AMD ReLive
- My video timing doesn't match demo? → Start recording BEFORE joining match
- Can I change clip padding? → Yes, edit config.py (default: 5sec before, 3sec after)
- Clips are too long/short? → Adjust TICKS_PER_SECOND or padding in config
