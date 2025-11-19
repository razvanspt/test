"""
Main FastAPI Application
Similar to @SpringBootApplication main class in Spring Boot

This is the entry point of the backend application.
It defines REST API endpoints (like @RestController in Spring).
"""

import logging
import time
import uuid
from pathlib import Path
from typing import List
import platform
import gc

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import our service classes (like @Autowired in Spring)
from demo_parser_service import DemoParserService
from faceit_demo_parser_service import FaceItDemoParserService
from highlight_detector_service import HighlightDetectorService

# Import models (DTOs)
from models import DemoAnalysisResponse, ErrorResponse, HighlightMoment

# Import configuration
from config import (
    API_HOST,
    API_PORT,
    CORS_ORIGINS,
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    DEMO_UPLOAD_DIR,
    MAX_UPLOAD_SIZE,
    ALLOWED_EXTENSIONS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === APPLICATION INITIALIZATION ===

# Create FastAPI app instance
# In Spring Boot: @SpringBootApplication public class Application { ... }
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/api/docs",  # Swagger UI (like Springdoc OpenAPI)
    redoc_url="/api/redoc"  # Alternative API documentation
)

# Add CORS middleware
# Allows frontend to call backend from different port/domain
# In Spring: @CrossOrigin(origins = {"http://localhost:3000"})
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# === SERVICE INITIALIZATION ===
# Create service instances (singleton pattern)
# In Spring Boot, these would be @Autowired
demo_parser_service = DemoParserService()
faceit_parser_service = FaceItDemoParserService()
highlight_detector_service = HighlightDetectorService()

# === UTILITY FUNCTIONS ===

def safe_delete_file(file_path: Path, max_retries: int = 5) -> bool:
    """
    Safely delete a file with retry logic for Windows file locking

    On Windows, demo parsers (esp. Rust-based like demoparser2) can keep
    file handles open even after the parser is deleted. This function
    retries deletion with increasing delays to allow the OS to release locks.

    Args:
        file_path: Path to file to delete
        max_retries: Maximum number of retry attempts

    Returns:
        True if file was deleted successfully, False otherwise
    """
    is_windows = platform.system() == "Windows"

    for attempt in range(max_retries):
        try:
            if file_path.exists():
                file_path.unlink()
            return True
        except PermissionError as e:
            if attempt < max_retries - 1 and is_windows:
                # On Windows, force GC and wait before retrying
                gc.collect()
                delay = 0.1 * (2 ** attempt)  # Exponential backoff: 0.1, 0.2, 0.4, 0.8, 1.6s
                logger.warning(f"File locked, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                logger.error(f"Failed to delete {file_path}: {e}")
                return False
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")
            return False

    return False


def validate_demo_file(filename: str) -> bool:
    """
    Validate that uploaded file is a .dem file

    In Java:
    private boolean validateDemoFile(String filename)

    Args:
        filename: Name of uploaded file

    Returns:
        True if valid, False otherwise
    """
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    return extension in ALLOWED_EXTENSIONS


# === API ENDPOINTS (REST Controllers) ===

@app.get("/")
async def root():
    """
    Root endpoint - health check

    In Spring:
    @GetMapping("/")
    public Map<String, String> root()

    Returns basic API info
    """
    return {
        "message": "CS2 Highlight Generator API",
        "version": APP_VERSION,
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint

    In Spring:
    @GetMapping("/api/health")
    public ResponseEntity<Map<String, String>> healthCheck()

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@app.post(
    "/api/analyze-demo",
    response_model=DemoAnalysisResponse,
    responses={
        200: {"description": "Demo analyzed successfully"},
        400: {"description": "Invalid file or bad request"},
        500: {"description": "Internal server error"}
    }
)
async def analyze_demo(file: UploadFile = File(...)):
    """
    Main endpoint: Upload and analyze a CS2 demo file

    In Spring:
    @PostMapping("/api/analyze-demo")
    public ResponseEntity<DemoAnalysisResponse> analyzeDemo(
        @RequestParam("file") MultipartFile file
    )

    This endpoint:
    1. Receives uploaded .dem file
    2. Parses the demo file
    3. Detects highlights
    4. Returns analysis results

    Args:
        file: Uploaded .dem file (multipart/form-data)

    Returns:
        DemoAnalysisResponse with highlights and stats

    Raises:
        HTTPException: If file is invalid or processing fails
    """
    logger.info(f"Received demo upload: {file.filename}")
    start_time = time.time()

    # === VALIDATION ===

    # Check file extension
    if not validate_demo_file(file.filename):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only .dem files are allowed."
        )

    # Check file size (read in chunks to avoid memory issues)
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    try:
        # Generate unique ID for this demo
        demo_id = str(uuid.uuid4())

        # Save uploaded file
        file_path = DEMO_UPLOAD_DIR / f"{demo_id}.dem"

        logger.info(f"Saving demo to: {file_path}")

        # Write file in chunks
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                file_size += len(chunk)

                # Check if file is too large
                if file_size > MAX_UPLOAD_SIZE:
                    logger.warning(f"File too large: {file_size} bytes")
                    # Delete partial file
                    safe_delete_file(file_path)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE / 1024 / 1024}MB"
                    )

                f.write(chunk)

        logger.info(f"File saved successfully ({file_size / 1024 / 1024:.2f}MB)")

        # === DEMO PARSING ===

        logger.info("Starting demo parsing...")
        try:
            # Parse the demo file using our service
            # This can take 10-30 seconds for a full match
            parsed_data = demo_parser_service.parse_demo_file(file_path)

            # Extract parsed components
            raw_demo_data = parsed_data["raw_data"]
            match_info = parsed_data["match_info"]
            player_stats = parsed_data["player_stats"]

        except Exception as e:
            logger.error(f"Demo parsing failed: {str(e)}", exc_info=True)
            # Clean up file
            safe_delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse demo: {str(e)}"
            )

        # === HIGHLIGHT DETECTION ===

        logger.info("Starting highlight detection...")
        try:
            # Get rounds and kills data
            rounds_data = demo_parser_service.get_rounds_data(raw_demo_data)
            kills_data = demo_parser_service.get_kills_data(raw_demo_data)

            # Detect highlights using our service
            highlights = highlight_detector_service.detect_highlights(
                rounds_data=rounds_data,
                kills_data=kills_data
            )

        except Exception as e:
            logger.error(f"Highlight detection failed: {str(e)}", exc_info=True)
            # Continue anyway, just return empty highlights
            highlights = []

        # === RESPONSE PREPARATION ===

        processing_time = time.time() - start_time
        logger.info(f"Demo analysis completed in {processing_time:.2f} seconds")
        logger.info(f"Found {len(highlights)} highlights")

        # Build response
        response = DemoAnalysisResponse(
            success=True,
            message=f"Demo analyzed successfully. Found {len(highlights)} highlights.",
            match_info=match_info,
            highlights=highlights,
            player_stats=player_stats,
            demo_file_id=demo_id,
            processing_time_seconds=round(processing_time, 2)
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@app.post(
    "/api/analyze-demo-faceit",
    response_model=DemoAnalysisResponse,
    responses={
        200: {"description": "FaceIt demo analyzed successfully"},
        400: {"description": "Invalid file or bad request"},
        500: {"description": "Internal server error"}
    }
)
async def analyze_faceit_demo(file: UploadFile = File(...)):
    """
    Specialized endpoint for FaceIt CS2 demos

    FaceIt servers use custom configurations that don't emit standard events
    like 'round_officially_ended', which breaks normal awpy parsing. This
    endpoint uses alternative parsing strategies to extract highlights from
    FaceIt demos.

    In Spring:
    @PostMapping("/api/analyze-demo-faceit")
    public ResponseEntity<DemoAnalysisResponse> analyzeFaceItDemo(
        @RequestParam("file") MultipartFile file
    )

    Args:
        file: Uploaded .dem file from FaceIt

    Returns:
        DemoAnalysisResponse with highlights and stats

    Raises:
        HTTPException: If file is invalid or processing fails
    """
    logger.info(f"Received FaceIt demo upload: {file.filename}")
    start_time = time.time()

    # Validate file
    if not validate_demo_file(file.filename):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only .dem files are allowed."
        )

    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    try:
        # Generate unique ID
        demo_id = str(uuid.uuid4())
        file_path = DEMO_UPLOAD_DIR / f"{demo_id}_faceit.dem"

        logger.info(f"Saving FaceIt demo to: {file_path}")

        # Save file
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                file_size += len(chunk)

                if file_size > MAX_UPLOAD_SIZE:
                    logger.warning(f"File too large: {file_size} bytes")
                    safe_delete_file(file_path)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE / 1024 / 1024}MB"
                    )

                f.write(chunk)

        logger.info(f"FaceIt demo saved ({file_size / 1024 / 1024:.2f}MB)")

        # === FACEIT DEMO PARSING ===

        logger.info("Starting FaceIt demo parsing...")
        try:
            parsed_data = faceit_parser_service.parse_faceit_demo(file_path)

            raw_demo_data = parsed_data["raw_data"]
            match_info = parsed_data["match_info"]
            player_stats = parsed_data["player_stats"]

        except Exception as e:
            logger.error(f"FaceIt demo parsing failed: {str(e)}", exc_info=True)
            safe_delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse FaceIt demo: {str(e)}"
            )

        # === HIGHLIGHT DETECTION ===

        logger.info("Detecting highlights in FaceIt demo...")
        try:
            kills_data = faceit_parser_service.get_kills_data(raw_demo_data)

            # For FaceIt, we don't have proper rounds, so we pass empty rounds
            # Highlight detection will work with just kills data
            highlights = highlight_detector_service.detect_highlights(
                rounds_data=[],  # No round data from FaceIt
                kills_data=kills_data
            )

        except Exception as e:
            logger.error(f"Highlight detection failed: {str(e)}", exc_info=True)
            highlights = []

        # === RESPONSE ===

        processing_time = time.time() - start_time
        logger.info(f"✓ FaceIt demo analysis completed in {processing_time:.2f} seconds")
        logger.info(f"  Found {len(highlights)} highlights")

        response = DemoAnalysisResponse(
            success=True,
            message=f"FaceIt demo analyzed successfully. Found {len(highlights)} highlights.",
            match_info=match_info,
            highlights=highlights,
            player_stats=player_stats,
            demo_file_id=demo_id,
            processing_time_seconds=round(processing_time, 2)
        )

        return response

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Unexpected error processing FaceIt demo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@app.get("/api/highlights/{demo_id}")
async def get_highlights(demo_id: str):
    """
    Get highlights for a previously analyzed demo

    In Spring:
    @GetMapping("/api/highlights/{demoId}")
    public ResponseEntity<List<HighlightMoment>> getHighlights(
        @PathVariable String demoId
    )

    Note: For MVP, we're not storing results in a database,
    so this endpoint will return a "not implemented" message.
    In Phase 2, you would store results in PostgreSQL.

    Args:
        demo_id: Unique ID of the demo

    Returns:
        List of highlights (when implemented)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Highlight storage not yet implemented. Re-upload demo to analyze."
    )


@app.post("/api/export/ffmpeg-script")
async def export_ffmpeg_script(highlights: List[dict]):
    """
    Generate FFmpeg shell script to extract video clips from highlights

    This endpoint takes the highlights JSON from /api/analyze and generates
    a bash script with FFmpeg commands to cut clips from a gameplay recording.

    Usage:
    1. Upload .dem file to /api/analyze -> get highlights JSON
    2. POST highlights to this endpoint -> get bash script
    3. Run script with your gameplay video: ./script.sh video.mp4

    Args:
        highlights: List of highlight dicts from analysis response

    Returns:
        Plain text bash script

    Example:
        curl -X POST http://localhost:8000/api/export/ffmpeg-script \\
             -H "Content-Type: application/json" \\
             -d '[{"type":"ACE","round":3,"start_time":145.2,...}]' \\
             > extract_highlights.sh
        chmod +x extract_highlights.sh
        ./extract_highlights.sh my_gameplay.mp4
    """
    try:
        if not highlights or len(highlights) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No highlights provided"
            )

        # Generate script header
        script = "#!/bin/bash\n"
        script += "# CS2 Highlight Extractor - Auto-generated FFmpeg script\n"
        script += f"# Generated for {len(highlights)} highlights\n"
        script += "#\n"
        script += "# USAGE: ./extract_highlights.sh <your_gameplay_video.mp4>\n"
        script += "#\n"
        script += "# IMPORTANT: Your gameplay video must be synchronized with the demo!\n"
        script += "#            Start recording BEFORE the match starts.\n"
        script += "#\n"
        script += "# Requirements:\n"
        script += "#   - FFmpeg installed (brew install ffmpeg / apt install ffmpeg)\n"
        script += "#   - Enough disk space for clips\n"
        script += "#\n\n"

        script += 'if [ -z "$1" ]; then\n'
        script += '    echo "❌ Error: No input video specified"\n'
        script += '    echo ""\n'
        script += '    echo "Usage: $0 <your_gameplay_video.mp4>"\n'
        script += '    echo ""\n'
        script += f'    echo "This script will extract {len(highlights)} highlight clips from your video."\n'
        script += '    echo ""\n'
        script += '    exit 1\n'
        script += 'fi\n\n'

        script += 'INPUT_VIDEO="$1"\n'
        script += 'OUTPUT_DIR="highlight_clips"\n\n'

        script += '# Check if input video exists\n'
        script += 'if [ ! -f "$INPUT_VIDEO" ]; then\n'
        script += '    echo "❌ Error: Video file not found: $INPUT_VIDEO"\n'
        script += '    exit 1\n'
        script += 'fi\n\n'

        script += '# Check if FFmpeg is installed\n'
        script += 'if ! command -v ffmpeg &> /dev/null; then\n'
        script += '    echo "❌ Error: FFmpeg is not installed"\n'
        script += '    echo ""\n'
        script += '    echo "Install FFmpeg:"\n'
        script += '    echo "  macOS:   brew install ffmpeg"\n'
        script += '    echo "  Ubuntu:  sudo apt install ffmpeg"\n'
        script += '    echo "  Windows: Download from https://ffmpeg.org/download.html"\n'
        script += '    echo ""\n'
        script += '    exit 1\n'
        script += 'fi\n\n'

        script += '# Create output directory\n'
        script += 'mkdir -p "$OUTPUT_DIR"\n\n'

        script += 'echo "╔══════════════════════════════════════════════════════════════╗"\n'
        script += 'echo "║  CS2 Highlight Clip Extractor                                ║"\n'
        script += 'echo "╚══════════════════════════════════════════════════════════════╝"\n'
        script += f'echo "Input video: $INPUT_VIDEO"\n'
        script += f'echo "Total highlights: {len(highlights)}"\n'
        script += 'echo "Output directory: $OUTPUT_DIR/"\n'
        script += 'echo ""\n\n'

        # Generate FFmpeg commands for each highlight
        for i, highlight in enumerate(highlights, 1):
            start_time = highlight.get("start_time", 0)
            end_time = highlight.get("end_time", 0)
            duration = end_time - start_time

            hl_type = highlight.get("type", "HIGHLIGHT")
            round_num = highlight.get("round", 0)
            player = highlight.get("player", "Unknown")
            description = highlight.get("description", f"Highlight {i}")

            # Sanitize player name for filename (remove special chars)
            safe_player = "".join(c for c in player if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_player = safe_player.replace(' ', '_')

            output_file = f"highlight_{i:02d}_{hl_type}_round{round_num}_{safe_player}.mp4"

            script += f'# ────────────────────────────────────────────────────────────────\n'
            script += f'# Highlight {i}/{len(highlights)}: {description}\n'
            script += f'# Round: {round_num} | Player: {player}\n'
            script += f'# Time: {start_time:.1f}s - {end_time:.1f}s (duration: {duration:.1f}s)\n'
            script += f'# ────────────────────────────────────────────────────────────────\n'
            script += f'echo "📹 Extracting clip {i}/{len(highlights)}: {description}"\n'

            # FFmpeg command
            # -ss before -i for fast seeking
            # -t for duration
            # -c:v libx264 -preset fast -crf 18 for good quality
            # -c:a aac for audio
            script += f'ffmpeg -y -loglevel warning -stats \\\n'
            script += f'  -ss {start_time} \\\n'
            script += f'  -i "$INPUT_VIDEO" \\\n'
            script += f'  -t {duration} \\\n'
            script += f'  -c:v libx264 -preset fast -crf 18 \\\n'
            script += f'  -c:a aac -b:a 192k \\\n'
            script += f'  "$OUTPUT_DIR/{output_file}"\n\n'

            script += f'if [ $? -eq 0 ]; then\n'
            script += f'    echo "✅ Created: {output_file}"\n'
            script += f'else\n'
            script += f'    echo "❌ Failed to create: {output_file}"\n'
            script += f'fi\n'
            script += f'echo ""\n\n'

        # Footer
        script += 'echo "╔══════════════════════════════════════════════════════════════╗"\n'
        script += 'echo "║  Extraction Complete!                                        ║"\n'
        script += 'echo "╚══════════════════════════════════════════════════════════════╝"\n'
        script += 'echo ""\n'
        script += 'echo "📂 Clips saved to: $OUTPUT_DIR/"\n'
        script += 'echo ""\n'
        script += 'ls -lh "$OUTPUT_DIR/" | grep -v "^total"\n'
        script += 'echo ""\n'
        script += f'echo "✅ Generated {len(highlights)} highlight clips"\n'

        logger.info(f"Generated FFmpeg script for {len(highlights)} highlights")

        # Return as plain text script
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=script,
            media_type="text/x-shellscript",
            headers={
                "Content-Disposition": "attachment; filename=extract_highlights.sh"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating FFmpeg script: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate script: {str(e)}"
        )


# === APPLICATION ENTRY POINT ===

def main():
    """
    Start the FastAPI server

    In Spring Boot:
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
    """
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Server will be available at http://{API_HOST}:{API_PORT}")
    logger.info(f"API documentation at http://{API_HOST}:{API_PORT}/api/docs")

    # Run the server using uvicorn (ASGI server)
    # Similar to running embedded Tomcat in Spring Boot
    uvicorn.run(
        "main:app",  # Module:app_instance
        host=API_HOST,
        port=API_PORT,
        reload=True,  # Auto-reload on code changes (dev mode only)
        log_level="info"
    )


# This runs when you execute: python main.py
if __name__ == "__main__":
    main()
