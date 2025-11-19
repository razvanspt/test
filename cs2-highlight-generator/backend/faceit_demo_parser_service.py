"""
FaceIt Demo Parser Service
Specialized service for parsing FaceIt CS2 demos using awpy without round parsing

FaceIt servers use custom configurations and don't emit standard events like
'round_officially_ended', which breaks awpy's round parsing. This service
uses awpy's parse_events() method to extract kill events directly without
relying on round parsing.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any
import time

# Use awpy but bypass the full parse() method that requires rounds
from awpy import Demo
import awpy.parsers.utils
import awpy.parsers.events

from models import MatchInfo, PlayerStats

logger = logging.getLogger(__name__)


class FaceItDemoParserService:
    """
    Specialized parser for FaceIt demos using awpy's parse_events()

    In Java:
    @Service
    public class FaceItDemoParserService {
        public DemoData parseFaceItDemo(File demoFile) { ... }
    }
    """

    def __init__(self):
        """Constructor"""
        logger.info("FaceItDemoParserService initialized (using awpy.parse_events)")

    def parse_faceit_demo(self, demo_file_path: Path) -> Dict[str, Any]:
        """
        Parse a FaceIt CS2 demo file using awpy's parse_events() method

        This bypasses awpy's full parse() which requires round parsing.
        We extract kill events directly from the demo without needing rounds.

        Args:
            demo_file_path: Path to the .dem file

        Returns:
            Dictionary containing kills, damages, and basic match info

        Raises:
            Exception: If parsing fails completely
        """
        logger.info(f"Parsing FaceIt demo with awpy.parse_events(): {demo_file_path}")
        start_time = time.time()

        try:
            if not demo_file_path.exists():
                raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

            # Initialize awpy Demo object
            demo = Demo(path=str(demo_file_path), verbose=True)

            logger.info("Extracting all events from FaceIt demo...")

            # Use parse_events() to get raw events without requiring round parsing
            # This method extracts events directly from the demo file
            events_dict = demo.parse_events()

            logger.info(f"✓ Extracted {len(events_dict)} event types")
            logger.info(f"Event types available: {list(events_dict.keys())}")

            # Extract player_death events using awpy's utility function
            # This is the same approach awpy uses internally for demo.kills
            if "player_death" in events_dict:
                raw_kills = events_dict["player_death"]
                logger.info(f"✓ Found {len(raw_kills)} player_death events")

                # Use awpy's parse_kills() to standardize the kill data
                # This renames "user_" columns to "victim_" and processes hitgroups
                kills_df = awpy.parsers.events.parse_kills(raw_kills)

                logger.info(f"DataFrame columns: {list(kills_df.columns)}")

                # Log first kill to see data structure
                if len(kills_df) > 0:
                    logger.info(f"Sample kill data (first 3 columns): {kills_df.iloc[0][:3].to_dict()}")

                # Convert to list of dictionaries
                kills = kills_df.to_dict('records')
            else:
                logger.warning("No player_death events found in demo!")
                kills = []

            # Extract map name from header
            map_name = demo.header.get("map_name", "Unknown") if hasattr(demo, 'header') else "Unknown"

            # Determine total rounds from kills data
            # Look for a round-related field in the kills
            total_rounds = 0
            if len(kills) > 0:
                # Check various possible round number fields
                round_fields = ['round_num', 'round', 'total_rounds_played']
                for field in round_fields:
                    if field in kills[0]:
                        total_rounds = max([k.get(field, 0) for k in kills]) + 1
                        break

            # If still 0, estimate from tick data
            if total_rounds == 0 and len(kills) > 0:
                # CS2 rounds are typically ~120 seconds at 128 tick/sec = ~15,360 ticks
                # Estimate rounds from tick span
                if 'tick' in kills[0]:
                    max_tick = max([k.get('tick', 0) for k in kills])
                    total_rounds = max(1, int(max_tick / 15360))

            elapsed = time.time() - start_time
            logger.info(f"✓ FaceIt demo parsed successfully in {elapsed:.2f} seconds")
            logger.info(f"  Found {len(kills)} kills across ~{total_rounds} rounds")

            # Build a data structure compatible with the existing highlight detector
            demo_data = {
                "header": {"map_name": map_name},
                "kills": kills,
                "damages": [],  # Not needed for highlight detection yet
                "bomb": [],     # Not needed for highlight detection yet
                "rounds": []    # FaceIt demos don't have reliable round data
            }

            # Extract match info
            match_info = self._extract_faceit_match_info(demo_data, total_rounds)

            # Extract player stats
            player_stats = self._extract_faceit_player_stats(demo_data)

            return {
                "raw_data": demo_data,
                "match_info": match_info,
                "player_stats": player_stats,
                "parsing_time": elapsed
            }

        except Exception as e:
            logger.error(f"FaceIt demo parsing failed: {str(e)}", exc_info=True)
            raise Exception(
                f"Failed to parse FaceIt demo with awpy.parse_events().\n\n"
                f"Error: {str(e)}\n\n"
                f"This could be due to:\n"
                f"1. Demo file is corrupted or incomplete\n"
                f"2. Demo is from an unsupported CS2 version\n"
                f"3. Demo file is actually from CS:GO (not CS2)\n\n"
                f"Please try:\n"
                f"- A different FaceIt demo\n"
                f"- A more recent demo (last 30 days)\n"
                f"- Updating awpy: pip install --upgrade awpy"
            )

    def _extract_faceit_match_info(self, demo_data: Dict, total_rounds: int) -> MatchInfo:
        """Extract match info from FaceIt demo data"""
        try:
            header = demo_data.get("header", {})
            map_name = header.get("map_name", "Unknown")

            # Estimate duration based on rounds (CS2 rounds avg ~2 minutes)
            duration_minutes = total_rounds * 2.0

            return MatchInfo(
                map_name=map_name,
                total_rounds=total_rounds,
                team_1_score=0,  # Can't reliably determine from FaceIt demos
                team_2_score=0,  # Would need proper round end events
                duration_minutes=duration_minutes
            )
        except Exception as e:
            logger.warning(f"Error extracting FaceIt match info: {e}")
            return MatchInfo(
                map_name="Unknown",
                total_rounds=0,
                team_1_score=0,
                team_2_score=0,
                duration_minutes=0.0
            )

    def _extract_faceit_player_stats(self, demo_data: Dict) -> List[PlayerStats]:
        """Extract player stats from FaceIt demo data"""
        try:
            kills_data = demo_data.get("kills", [])
            player_stats_map: Dict[str, Dict] = {}

            # Debug: log all available fields in first kill
            if len(kills_data) > 0:
                logger.info(f"Available fields in kill data: {list(kills_data[0].keys())}")

            for kill in kills_data:
                # awpy's parse_kills() renames "user_" to "victim_"
                # So we should have fields like:
                # - attacker_name, victim_name
                # - attacker_steamid, victim_steamid
                # - weapon, headshot, etc.

                # Try different possible field names
                attacker_name = (
                    kill.get("attacker_name") or
                    kill.get("attacker_player_name") or
                    kill.get("attacker") or
                    "Unknown"
                )

                victim_name = (
                    kill.get("victim_name") or
                    kill.get("victim_player_name") or
                    kill.get("user_name") or  # fallback if parse_kills didn't rename
                    kill.get("victim") or
                    "Unknown"
                )

                is_headshot = kill.get("headshot", False) or kill.get("is_headshot", False)

                # Initialize stats
                if attacker_name not in player_stats_map:
                    player_stats_map[attacker_name] = {
                        "kills": 0,
                        "deaths": 0,
                        "headshots": 0
                    }

                if victim_name not in player_stats_map:
                    player_stats_map[victim_name] = {
                        "kills": 0,
                        "deaths": 0,
                        "headshots": 0
                    }

                # Update stats
                player_stats_map[attacker_name]["kills"] += 1
                if is_headshot:
                    player_stats_map[attacker_name]["headshots"] += 1

                player_stats_map[victim_name]["deaths"] += 1

            # Convert to PlayerStats objects
            player_stats_list = []
            for player_name, stats in player_stats_map.items():
                kills = stats["kills"]
                headshots = stats["headshots"]
                hs_percentage = (headshots / kills * 100) if kills > 0 else 0.0

                player_stats_list.append(PlayerStats(
                    name=player_name,
                    kills=kills,
                    deaths=stats["deaths"],
                    assists=0,  # Would need assist events to calculate
                    headshot_percentage=round(hs_percentage, 2),
                    adr=0.0  # Would need damage events to calculate
                ))

            # Sort by kills
            player_stats_list.sort(key=lambda p: p.kills, reverse=True)

            return player_stats_list

        except Exception as e:
            logger.warning(f"Error extracting FaceIt player stats: {e}")
            logger.debug(f"Sample kill data: {kills_data[0] if kills_data else 'None'}")
            return []

    def get_kills_data(self, demo_data: Dict) -> List[Dict]:
        """Get kills data from parsed FaceIt demo"""
        return demo_data.get("kills", [])
