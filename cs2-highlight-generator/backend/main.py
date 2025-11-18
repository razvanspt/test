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

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import our service classes (like @Autowired in Spring)
from demo_parser_service import DemoParserService
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
highlight_detector_service = HighlightDetectorService()

# === UTILITY FUNCTIONS ===

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
                    file_path.unlink(missing_ok=True)
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
            file_path.unlink(missing_ok=True)
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
