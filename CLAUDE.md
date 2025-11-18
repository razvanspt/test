# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CS2 Highlight Generator - a prototype application that analyzes Counter-Strike 2 demo files to automatically detect and extract highlight moments (aces, multi-kills, clutches). The project is an MVP demonstrating the technical feasibility of a larger CS2 performance analytics platform.

## Architecture

### Two-Tier Architecture

**Backend (Python/FastAPI)**
- RESTful API server using FastAPI framework
- Demo file parsing using the `awpy` library (CS2 demo parser)
- Highlight detection through rule-based analysis
- Stateless processing - no database in MVP

**Frontend (Vanilla HTML/CSS/JS)**
- Single-page application with no framework dependencies
- Direct REST API calls to backend
- File upload interface for .dem files

### Data Flow

1. User uploads .dem file via frontend
2. Backend saves file with UUID, validates extension and size
3. `DemoParserService` parses demo using awpy library (10-30 seconds)
4. `HighlightDetectorService` analyzes rounds/kills to detect highlights
5. Response with match info, highlights, and player stats returned as JSON
6. Frontend displays results immediately (no persistence)

## Key Components

### Backend Services

**`demo_parser_service.py`** - Demo file parsing
- Uses awpy library to parse CS2 .dem files
- Extracts match info (map, rounds, scores)
- Extracts player stats (K/D, headshot %, ADR)
- Returns structured data for highlight detection

**`highlight_detector_service.py`** - Highlight detection
- Rule-based detection (no ML in MVP)
- Detects: aces (5K), 4K, 3K events
- Calculates timestamps using tick data (128 ticks/second)
- Returns HighlightMoment objects with metadata

**`timestamp_exporter.py`** - Export utilities
- Formats highlights for external tools
- Supports JSON, FFmpeg scripts, YouTube chapters

### Models (`models.py`)

Uses Pydantic for type validation (similar to Java Bean Validation):
- `HighlightMoment` - Single highlight with tick/time data
- `MatchInfo` - Match metadata (map, score, duration)
- `PlayerStats` - Per-player statistics
- `DemoAnalysisResponse` - Complete API response

### Configuration (`config.py`)

Centralized settings:
- API host/port (default: 0.0.0.0:8000)
- File upload constraints (max 100MB, .dem only)
- Directory paths for uploads and output

## Development Commands

### Setup and Installation

```bash
# Install backend dependencies
cd cs2-highlight-generator/backend
pip install -r requirements.txt
```

### Running the Application

```bash
# Start backend server (from backend/ directory)
python main.py

# Or use the convenience script (from project root)
./start.sh
```

Server runs at `http://localhost:8000` with auto-reload enabled.

### Testing

Open `cs2-highlight-generator/frontend/index.html` in a browser to test the upload interface.

API docs available at `http://localhost:8000/api/docs` (Swagger UI).

### Uploading Test Demos

CS2 demo files (.dem) can be obtained from:
- CS2 client: Watch → Your Matches → Download
- HLTV.org (professional matches)

## Important Technical Details

### Demo Parsing Performance

- Short demos (10 rounds): ~5 seconds
- Full matches (30 rounds): ~15-25 seconds
- Overtime (40+ rounds): ~30-40 seconds

The parsing happens synchronously - this blocks the API endpoint. For production, implement async job queue (Celery/RQ).

### Tick System

CS2 uses tick-based timing (128 ticks/second on official servers):
- Tick timestamps in demo files are integers
- Convert to seconds: `time_seconds = tick / 128`
- Highlights store both tick and time for precision

### File Handling

- Files saved with UUID to `demo_files/` directory
- No cleanup implemented in MVP - files persist
- For production, implement retention policy or post-processing cleanup

### awpy Library Quirks

- First install takes 2-5 minutes (downloads parsing libraries)
- Returns complex nested dictionaries - navigate carefully
- Some demo files may fail to parse (corruption, version mismatch)
- Always wrap parsing in try/except blocks

## Future Development Notes

### Phase 2 Additions (From Roadmap)

1. **Database Integration** - Add PostgreSQL for match history
2. **Clutch Detection** - Analyze player counts per round
3. **Video Generation** - FFmpeg integration for clip creation
4. **User Accounts** - Steam OAuth authentication
5. **Job Queue** - Async processing with Celery

### Known Limitations

- No persistence - re-upload required to re-analyze
- No clutch detection (only multi-kill detection)
- No video generation (only timestamp extraction)
- Synchronous processing (blocks during parse)
- No user accounts or match history

### Architecture Considerations

The codebase is designed for easy migration:
- Service layer pattern enables database integration
- Models use Pydantic for validation
- Config centralization simplifies environment changes
- FastAPI's async support ready for background jobs

## Code Style Notes

### For Java Developers

This codebase includes extensive comments mapping Python concepts to Java equivalents:
- `@app.post()` → `@PostMapping()`
- `BaseModel` → POJO/Entity
- `List[str]` → `List<String>`
- Service classes follow Spring Boot patterns

### Python Conventions

- Type hints used throughout (`: str`, `-> int`)
- Async/await for file I/O operations
- F-strings for string formatting
- Pathlib for file path handling
- Logging instead of print statements

## Related Documentation

- Full project analysis: `CS2_APP_ANALYSIS.md`
- Setup guide: `cs2-highlight-generator/QUICKSTART.md`
- Detailed features: `cs2-highlight-generator/README.md`
- awpy documentation: https://awpy.readthedocs.io/
