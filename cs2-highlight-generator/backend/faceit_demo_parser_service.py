"""
FaceIt Demo Parser Service
Specialized service for parsing FaceIt CS2 demos using demoparser2 directly

FaceIt servers use custom configurations and don't emit standard events like
'round_officially_ended', which breaks awpy's round parsing. This service
uses demoparser2 (the underlying parser) directly to extract kill events
without relying on round parsing.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any
import time

# Use demoparser2 directly instead of awpy to bypass round parsing issues
from demoparser2 import DemoParser

from models import MatchInfo, PlayerStats

logger = logging.getLogger(__name__)


class FaceItDemoParserService:
    """
    Specialized parser for FaceIt demos using demoparser2 directly

    In Java:
    @Service
    public class FaceItDemoParserService {
        public DemoData parseFaceItDemo(File demoFile) { ... }
    }
    """

    def __init__(self):
        """Constructor"""
        logger.info("FaceItDemoParserService initialized (using demoparser2 directly)")

    def parse_faceit_demo(self, demo_file_path: Path) -> Dict[str, Any]:
        """
        Parse a FaceIt CS2 demo file using demoparser2 directly

        This bypasses awpy's round parsing which fails on FaceIt demos.
        We extract kill events directly from the demo without needing rounds.

        Args:
            demo_file_path: Path to the .dem file

        Returns:
            Dictionary containing kills, damages, and basic match info

        Raises:
            Exception: If parsing fails completely
        """
        logger.info(f"Parsing FaceIt demo with demoparser2: {demo_file_path}")
        start_time = time.time()

        try:
            if not demo_file_path.exists():
                raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

            # Initialize demoparser2 directly
            parser = DemoParser(str(demo_file_path))

            # Parse player_death events to get all kills
            # Request key fields we need for highlight detection
            logger.info("Extracting player_death events from FaceIt demo...")

            kills_df = parser.parse_event(
                "player_death",
                player=["X", "Y", "Z"],  # Player positions
                other=["total_rounds_played", "game_time"]  # Round info and timestamp
            )

            logger.info(f"✓ Extracted {len(kills_df)} player_death events")

            # Convert DataFrame to list of dictionaries for compatibility with existing code
            # The DataFrame columns will include event fields + requested player/other fields
            kills = kills_df.to_dict('records')

            # Extract map name from header if available
            map_name = "Unknown"
            try:
                # Parse header separately to get map name
                # In demoparser2, we can extract this from game events
                header_df = parser.parse_event("round_start", other=["map_name"])
                if len(header_df) > 0:
                    map_name = header_df.iloc[0].get('map_name', 'Unknown')
            except Exception as e:
                logger.warning(f"Could not extract map name: {e}")

            # Get total rounds played from the kills data
            total_rounds = 0
            if len(kills) > 0:
                # The last kill should have the final round number
                total_rounds = max([k.get('total_rounds_played', 0) for k in kills]) + 1

            elapsed = time.time() - start_time
            logger.info(f"✓ FaceIt demo parsed successfully in {elapsed:.2f} seconds")
            logger.info(f"  Found {len(kills)} kills across {total_rounds} rounds")

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
                f"Failed to parse FaceIt demo with demoparser2.\n\n"
                f"Error: {str(e)}\n\n"
                f"This could be due to:\n"
                f"1. Demo file is corrupted or incomplete\n"
                f"2. Demo is from an unsupported CS2 version\n"
                f"3. Demo file is actually from CS:GO (not CS2)\n\n"
                f"Please try:\n"
                f"- A different FaceIt demo\n"
                f"- A more recent demo (last 30 days)\n"
                f"- Updating awpy/demoparser2: pip install --upgrade awpy demoparser2"
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

            for kill in kills_data:
                # The DataFrame columns might use different names
                # demoparser2 returns attacker/victim info in the event
                # We need to check what fields are actually available

                # Try different possible field names for attacker/victim
                attacker_name = (
                    kill.get("attacker_name") or
                    kill.get("attacker") or
                    kill.get("user_name") or
                    "Unknown"
                )

                victim_name = (
                    kill.get("victim_name") or
                    kill.get("userid_name") or
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
