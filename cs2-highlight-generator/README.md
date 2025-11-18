# CS2 Highlight Generator - MVP Prototype

**Automatically detect and extract highlights from CS2 demo files**

This is a working prototype that parses Counter-Strike 2 demo files and automatically detects highlight moments like aces, multi-kills, and clutches.

---

## Features

### Current (MVP)
- ✅ Upload CS2 demo files (.dem)
- ✅ Automatic parsing of demo data
- ✅ Highlight detection:
  - Aces (5 kills in a round)
  - 4K (4 kills)
  - 3K (3 kills)
- ✅ Match statistics (map, score, duration)
- ✅ Player statistics (K/D, headshot %)
- ✅ Simple web interface
- ✅ REST API
- ✅ Timestamp export for video editing

### Planned (Phase 2)
- ⏳ Clutch detection (1vX situations)
- ⏳ High damage round detection
- ⏳ Automated video clip generation
- ⏳ Multiple output formats (TikTok, YouTube Shorts, etc.)
- ⏳ User accounts and match history
- ⏳ Database storage
- ⏳ Social features

---

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI (web framework)
- awpy (CS2 demo parser)
- Pydantic (data validation)

**Frontend:**
- HTML5 + CSS3 + Vanilla JavaScript
- No framework dependencies

**Future:**
- PostgreSQL (database)
- FFmpeg (video processing)
- React (better frontend)

---

## Project Structure

```
cs2-highlight-generator/
├── backend/
│   ├── main.py                      # FastAPI app (like Spring Boot @RestController)
│   ├── config.py                    # Configuration (like application.properties)
│   ├── models.py                    # Data models/DTOs (like POJOs)
│   ├── demo_parser_service.py       # Demo parsing service (like @Service)
│   ├── highlight_detector_service.py # Highlight detection service
│   ├── timestamp_exporter.py        # Export utility
│   └── requirements.txt             # Python dependencies
├── frontend/
│   └── index.html                   # Web interface
├── demo_files/                      # Uploaded demos stored here
├── output/                          # Processed output
└── README.md                        # This file
```

---

## Installation & Setup

### Prerequisites

1. **Python 3.11 or higher**
   - Check: `python3 --version`
   - Download: https://www.python.org/downloads/

2. **pip** (Python package manager)
   - Usually comes with Python
   - Check: `pip3 --version`

### Step 1: Install Python Dependencies

```bash
cd cs2-highlight-generator/backend
pip3 install -r requirements.txt
```

This will install:
- FastAPI (web framework)
- awpy (CS2 demo parser)
- uvicorn (ASGI server)
- Other dependencies

**Note:** First installation may take 2-5 minutes as awpy downloads CS2 parsing libraries.

### Step 2: Verify Installation

```bash
python3 -c "import awpy; print('awpy installed successfully')"
```

If you see "awpy installed successfully", you're good to go!

---

## Running the Application

### Start the Backend Server

```bash
cd cs2-highlight-generator/backend
python3 main.py
```

You should see:
```
INFO:     Starting CS2 Highlight Generator v1.0.0
INFO:     Server will be available at http://0.0.0.0:8000
INFO:     API documentation at http://0.0.0.0:8000/api/docs
```

The backend is now running on **http://localhost:8000**

### Open the Frontend

1. Open `cs2-highlight-generator/frontend/index.html` in your web browser
2. Or navigate to: `file:///path/to/cs2-highlight-generator/frontend/index.html`

---

## How to Use

### 1. Get a CS2 Demo File

**Option A: From Your Own Matches**
1. Play a CS2 match
2. After the match, go to "Watch" → "Your Matches"
3. Download the demo file (.dem)

**Option B: From Pro Matches**
1. Visit https://www.hltv.org/
2. Find a match
3. Download the demo file

### 2. Upload and Analyze

1. Open the web interface
2. Drag and drop your .dem file (or click to browse)
3. Click "Analyze Demo"
4. Wait 10-30 seconds (depending on match length)
5. View results!

### 3. Results

You'll see:
- **Match Info**: Map name, score, duration
- **Highlights**: All detected aces, 4Ks, 3Ks with timestamps
- **Player Stats**: K/D, headshot percentage for all players

---

## API Documentation

The backend provides a REST API you can use programmatically.

### Endpoints

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123
}
```

#### Analyze Demo
```http
POST /api/analyze-demo
Content-Type: multipart/form-data

file: <demo_file.dem>
```

**Response:**
```json
{
  "success": true,
  "message": "Demo analyzed successfully. Found 5 highlights.",
  "match_info": {
    "map_name": "de_mirage",
    "total_rounds": 24,
    "team_1_score": 13,
    "team_2_score": 11,
    "duration_minutes": 45.5
  },
  "highlights": [
    {
      "type": "ace",
      "round_number": 5,
      "start_tick": 150000,
      "end_tick": 152000,
      "start_time": 35.5,
      "end_time": 50.2,
      "player_name": "s1mple",
      "kills": 5,
      "damage": 500,
      "weapons_used": ["AK-47", "Desert Eagle"],
      "description": "s1mple ACE with AK-47 in round 5"
    }
  ],
  "player_stats": [...],
  "demo_file_id": "abc-123-def-456",
  "processing_time_seconds": 12.5
}
```

### Interactive API Docs

Visit **http://localhost:8000/api/docs** for interactive Swagger UI documentation.

You can test API endpoints directly from your browser!

---

## Code Explanation (For Java Developers)

Since you're familiar with Java, here's how the Python code maps to Java concepts:

| Python | Java Equivalent | Description |
|--------|----------------|-------------|
| `class MyService:` | `@Service public class MyService` | Service layer |
| `def my_method(self, arg: str) -> str:` | `public String myMethod(String arg)` | Method signature with types |
| `from models import User` | `import com.app.models.User;` | Import statement |
| `FastAPI()` | `@SpringBootApplication` | Web framework initialization |
| `@app.post("/api/endpoint")` | `@PostMapping("/api/endpoint")` | REST endpoint |
| `BaseModel` (Pydantic) | `@Entity` or POJO | Data model |
| `List[str]` | `List<String>` | Generic types |
| `Dict[str, int]` | `Map<String, Integer>` | Dictionary/Map |
| `raise HTTPException(...)` | `throw new HttpException(...)` | Exception handling |
| `async def` | `@Async` | Asynchronous method |

### Key Differences

1. **No semicolons** in Python
2. **Indentation matters** (replaces `{` `}`)
3. **Dynamic typing by default**, but we use type hints (`: str`, `-> int`)
4. **No `new` keyword** - just call the class name
5. **`self` instead of `this`**

---

## Troubleshooting

### "Module not found" errors

Make sure you're in the `backend/` directory and have installed dependencies:
```bash
cd backend
pip3 install -r requirements.txt
```

### "Port already in use" error

Another process is using port 8000. Either:
- Stop the other process
- Or edit `backend/config.py` and change `API_PORT = 8001`

### Demo parsing fails

- Ensure the .dem file is from CS2 (not CS:GO)
- File should be under 100MB
- Try a different demo file

### Slow parsing

- Normal for long matches (up to 30 seconds)
- Shorter demos (<20 rounds) should take <10 seconds

---

## Next Steps for Development

### Immediate Improvements (Week 1-2)

1. **Add clutch detection**
   - Analyze player counts in rounds
   - Detect 1v2, 1v3, 1v4, 1v5 situations

2. **Add high damage detection**
   - Parse damage events
   - Find rounds with 150+ damage

3. **Better error handling**
   - Validate demo files before parsing
   - Show progress during parsing

### Phase 2 (Month 2-3)

4. **Database Integration**
   - Add PostgreSQL
   - Store match results
   - User accounts (Steam OAuth)

5. **Video Generation**
   - Integrate FFmpeg
   - Auto-extract clips from gameplay recordings
   - Add transitions and effects

6. **Multiple Export Formats**
   - TikTok (9:16 vertical)
   - YouTube Shorts
   - Instagram Reels

### Phase 3 (Month 4+)

7. **React Frontend**
   - Replace HTML with React app
   - Better UI/UX
   - Mobile-friendly

8. **Social Features**
   - Highlight feed
   - Share highlights
   - Comments and likes

9. **Monetization**
   - Freemium model
   - Payment integration (Stripe)
   - Premium features

---

## How to Port to Java (If You Want)

The Python code is well-structured and commented. To port to Java:

1. **Backend Framework**: Use Spring Boot
   - `main.py` → `@RestController` classes
   - Services stay the same structure

2. **Demo Parsing**: Use the Go library with JNI
   - https://github.com/markus-wa/demoinfocs-golang
   - Create Java bindings

3. **Or**: Keep Python for demo parsing, use Java for everything else
   - Python microservice for parsing
   - Java main application
   - Communicate via REST API

**Recommendation**: Keep it in Python for now. The demo parsing libraries are mature and Python is easier for rapid prototyping. You can always port later.

---

## Exporting Timestamps for Video Editing

Use the `TimestampExporter` utility:

```python
from timestamp_exporter import TimestampExporter

# After getting highlights from API
exporter = TimestampExporter()

# Export as JSON
json_output = exporter.export_as_json(highlights)

# Export as FFmpeg script
ffmpeg_script = exporter.export_as_ffmpeg_script(highlights)

# Export as YouTube chapters
chapters = exporter.export_as_youtube_chapters(highlights)
```

This generates:
- **FFmpeg script**: Automate video cutting
- **JSON**: For custom processing
- **YouTube chapters**: For video descriptions

---

## Performance Notes

**Demo Parsing Speed:**
- Short demo (10 rounds): ~5 seconds
- Full match (30 rounds): ~15-25 seconds
- Overtime match (40+ rounds): ~30-40 seconds

**Bottlenecks:**
- Demo parsing (can't optimize much - library limitation)
- File upload (network speed)

**Future Optimizations:**
- Background job queue (Celery)
- Cache parsed demos
- Parallel processing for batch uploads

---

## Contributing Ideas

If you want to improve this prototype:

1. **Better Clutch Detection**
   - Analyze tick-by-tick player counts
   - Identify exact moment it became a clutch

2. **Weapon-Specific Highlights**
   - "Deagle Ace"
   - "AWP 4K"
   - "Knife Kill"

3. **Team Highlights**
   - "Triple spray transfer"
   - "Perfect execute with 4 kills"

4. **Round-Win Highlights**
   - Bomb defuses with <1 second
   - Clutch defuses

5. **Movement Highlights**
   - Bhop chains
   - Jump shots

---

## License

This is a prototype for learning and experimentation. Feel free to modify and extend!

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review code comments (extensively documented)
3. Check awpy documentation: https://awpy.readthedocs.io/

---

## Credits

- **awpy**: CS2 demo parsing library by pnxenopoulos
- **FastAPI**: Modern Python web framework
- **CS2**: Valve Corporation

---

**Built with ❤️ for the CS2 community**

*Now go find those epic aces! 🎯*
