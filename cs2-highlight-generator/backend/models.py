"""
Data Transfer Objects (DTOs) and Models
Similar to POJOs or Entity classes in Java

These classes define the structure of data passed between layers.
Pydantic is used for validation (similar to Java Bean Validation with @Valid)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# === ENUMS (similar to Java enum) ===

class HighlightType(str, Enum):
    """
    Types of highlights that can be detected
    In Java: public enum HighlightType { ACE, CLUTCH, ... }
    """
    ACE = "ace"  # 5 kills in a round
    QUADRA_KILL = "4k"  # 4 kills in a round
    TRIPLE_KILL = "3k"  # 3 kills in a round
    CLUTCH = "clutch"  # 1vX situation won
    HIGH_DAMAGE = "high_damage"  # High damage round (150+)


class VideoFormat(str, Enum):
    """
    Output video format options
    """
    TIKTOK = "tiktok"  # 9:16 vertical
    YOUTUBE_SHORTS = "youtube_shorts"  # 9:16 vertical
    INSTAGRAM_REEL = "instagram_reel"  # 9:16 vertical
    YOUTUBE = "youtube"  # 16:9 horizontal
    TWITTER = "twitter"  # 16:9 horizontal


# === REQUEST/RESPONSE MODELS ===

class HighlightMoment(BaseModel):
    """
    Represents a single highlight moment in a match
    In Java: public class HighlightMoment { ... }
    """
    # Type of highlight (ace, 3k, clutch, etc.)
    type: HighlightType = Field(..., description="Type of highlight")

    # Round number where this happened
    round_number: int = Field(..., ge=1, description="Round number (1-30)")

    # Tick in the demo file (for precise timestamp)
    # Ticks are CS2's internal time unit (128 ticks per second)
    start_tick: int = Field(..., description="Start tick of the highlight")
    end_tick: int = Field(..., description="End tick of the highlight")

    # Human-readable timestamps (in seconds from round start)
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")

    # Player who made the highlight
    player_name: str = Field(..., description="Player name")

    # Number of kills in this highlight
    kills: int = Field(..., ge=0, description="Number of kills")

    # Total damage dealt in this moment
    damage: int = Field(..., ge=0, description="Total damage dealt")

    # Was this a clutch? (1vX situation)
    is_clutch: bool = Field(default=False, description="Was this a clutch?")

    # Additional metadata
    weapons_used: List[str] = Field(default_factory=list, description="Weapons used")

    # Description for display
    description: str = Field(..., description="Human-readable description")

    class Config:
        # Allow this model to be used as a JSON schema
        json_schema_extra = {
            "example": {
                "type": "ace",
                "round_number": 5,
                "start_tick": 150000,
                "end_tick": 152000,
                "start_time": 35.5,
                "end_time": 50.2,
                "player_name": "s1mple",
                "kills": 5,
                "damage": 500,
                "is_clutch": False,
                "weapons_used": ["AK-47", "Desert Eagle"],
                "description": "s1mple ACE with AK-47 in round 5"
            }
        }


class PlayerStats(BaseModel):
    """
    Basic stats for a player in the match
    """
    name: str = Field(..., description="Player name")
    kills: int = Field(default=0, description="Total kills")
    deaths: int = Field(default=0, description="Total deaths")
    assists: int = Field(default=0, description="Total assists")
    headshot_percentage: float = Field(default=0.0, ge=0, le=100, description="Headshot %")
    adr: float = Field(default=0.0, description="Average Damage per Round")


class MatchInfo(BaseModel):
    """
    Information about the CS2 match
    """
    map_name: str = Field(..., description="Map name (e.g., de_mirage)")
    date: Optional[str] = Field(None, description="Match date")
    total_rounds: int = Field(..., description="Total rounds played")
    team_1_score: int = Field(default=0, description="Team 1 final score")
    team_2_score: int = Field(default=0, description="Team 2 final score")
    duration_minutes: float = Field(..., description="Match duration in minutes")


class DemoAnalysisResponse(BaseModel):
    """
    Response returned after analyzing a demo file
    This is what the API endpoint returns to the frontend
    In Java: public class DemoAnalysisResponse { ... }
    """
    # Success status
    success: bool = Field(..., description="Whether analysis succeeded")

    # Message for user
    message: str = Field(..., description="Status message")

    # Match information
    match_info: Optional[MatchInfo] = Field(None, description="Match metadata")

    # List of detected highlights
    highlights: List[HighlightMoment] = Field(default_factory=list, description="Detected highlights")

    # Player statistics
    player_stats: List[PlayerStats] = Field(default_factory=list, description="Player statistics")

    # File ID for reference (for future video generation)
    demo_file_id: Optional[str] = Field(None, description="Unique ID for this demo")

    # Processing time
    processing_time_seconds: float = Field(..., description="How long analysis took")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Demo analyzed successfully",
                "match_info": {
                    "map_name": "de_mirage",
                    "total_rounds": 24,
                    "team_1_score": 13,
                    "team_2_score": 11,
                    "duration_minutes": 45.5
                },
                "highlights": [],
                "player_stats": [],
                "demo_file_id": "abc123",
                "processing_time_seconds": 5.2
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response model
    """
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
