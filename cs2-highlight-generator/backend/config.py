"""
Configuration module for CS2 Highlight Generator
Similar to application.properties in Spring Boot

This file contains all configuration settings for the application.
In Java, this would be a @Configuration class or properties file.
"""

import os
from pathlib import Path

# === DIRECTORY CONFIGURATION ===
# Base directory of the project (like ${project.basedir} in Maven)
BASE_DIR = Path(__file__).parent.parent.resolve()

# Directory where uploaded demo files are stored
DEMO_UPLOAD_DIR = BASE_DIR / "demo_files"
DEMO_UPLOAD_DIR.mkdir(exist_ok=True)  # Create if doesn't exist

# Directory where processed output is stored
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# === FILE UPLOAD CONFIGURATION ===
# Maximum file size for demo uploads (100MB in bytes)
# Similar to spring.servlet.multipart.max-file-size
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB

# Allowed file extensions
ALLOWED_EXTENSIONS = {".dem"}  # Only CS2 demo files

# === HIGHLIGHT DETECTION CONFIGURATION ===
# Minimum kills for a highlight to be considered a "multi-kill"
MIN_MULTIKILL_KILLS = 3  # 3K or higher

# Maximum time between kills to be considered part of the same multi-kill (seconds)
MULTIKILL_TIME_WINDOW = 15.0

# Minimum damage in a round to be considered a "high damage round"
MIN_HIGH_DAMAGE = 150

# === API CONFIGURATION ===
# Server host and port (like server.port in Spring Boot)
API_HOST = "0.0.0.0"
API_PORT = 8000

# CORS settings - which origins can access the API
# In production, change this to your frontend domain
CORS_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# === APPLICATION INFO ===
APP_NAME = "CS2 Highlight Generator"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Automatically detect and extract highlights from CS2 demo files"

# === LOGGING CONFIGURATION ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # Can be DEBUG, INFO, WARNING, ERROR

# === DATABASE CONFIGURATION (for future expansion) ===
# Currently not used, but placeholder for when you add a database
# DATABASE_URL = "postgresql://user:password@localhost:5432/cs2highlights"
