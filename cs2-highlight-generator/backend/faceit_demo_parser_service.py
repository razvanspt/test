"""
FaceIt Demo Parser Service
Specialized service for parsing FaceIt CS2 demos using demoparser2 directly

FaceIt servers use custom configurations and don't emit standard events like
'round_officially_ended', which breaks awpy's round parsing. This service
uses demoparser2 directly to extract kill events without any field filtering.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any
import time

# Use demoparser2 directly - awpy's parse_events() fails on FaceIt demos
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

        This bypasses awpy completely since parse_events() fails on FaceIt demos.
        We extract kill events directly without any field filtering.

        Args:
            demo_file_path: Path to the .dem file

        Returns:
            Dictionary containing kills, damages, and basic match info

        Raises:
            Exception: If parsing fails completely
        """
        logger.info(f"Parsing FaceIt demo with demoparser2.parse_event(): {demo_file_path}")
        start_time = time.time()

        try:
            if not demo_file_path.exists():
                raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

            # Initialize demoparser2 directly
            parser = DemoParser(str(demo_file_path))

            logger.info("Extracting player_death events from FaceIt demo...")

            # Call parse_event WITHOUT field specifications to get ALL kills with ALL fields
            # The previous approach was filtering kills by requesting specific fields
            kills_df = parser.parse_event("player_death")

            logger.info(f"✓ Extracted {len(kills_df)} player_death events")
            logger.info(f"DataFrame shape: {kills_df.shape}")
            logger.info(f"DataFrame columns: {list(kills_df.columns)}")

            # Log first few kills to see data structure
            if len(kills_df) > 0:
                logger.info(f"First kill data:\n{kills_df.iloc[0]}")
                # Log column names that contain 'name' to find player name fields
                name_cols = [col for col in kills_df.columns if 'name' in col.lower()]
                logger.info(f"Columns containing 'name': {name_cols}")

            # Convert DataFrame to list of dictionaries
            kills = kills_df.to_dict('records')

            # Try to get map name
            map_name = "Unknown"
            try:
                # Attempt to get header info
                header_df = parser.parse_event("round_start")
                if len(header_df) > 0:
                    # Look for map name in columns
                    map_cols = [col for col in header_df.columns if 'map' in col.lower()]
                    logger.info(f"Map-related columns: {map_cols}")
                    if map_cols:
                        map_name = str(header_df.iloc[0][map_cols[0]])
            except Exception as e:
                logger.warning(f"Could not extract map name: {e}")

            # Determine total rounds from kills data
            total_rounds = 0
            if len(kills) > 0:
                # Check for various round number fields
                round_fields = [col for col in kills_df.columns if 'round' in col.lower()]
                logger.info(f"Round-related columns: {round_fields}")

                for field in round_fields:
                    try:
                        max_round = kills_df[field].max()
                        if max_round and max_round > 0:
                            total_rounds = int(max_round) + 1
                            logger.info(f"Using field '{field}' for round count: {total_rounds}")
                            break
                    except:
                        continue

            # If still 0, estimate from tick data
            if total_rounds == 0 and len(kills) > 0:
                tick_cols = [col for col in kills_df.columns if 'tick' in col.lower()]
                if tick_cols:
                    try:
                        max_tick = kills_df[tick_cols[0]].max()
                        # CS2 rounds ~120 sec at 128 tick/sec = ~15,360 ticks
                        total_rounds = max(1, int(max_tick / 15360))
                        logger.info(f"Estimated {total_rounds} rounds from tick data")
                    except:
                        total_rounds = 1

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
            player_stats = self._extract_faceit_player_stats(demo_data, kills_df)

            return {
                "raw_data": demo_data,
                "match_info": match_info,
                "player_stats": player_stats,
                "parsing_time": elapsed
            }

        except Exception as e:
            logger.error(f"FaceIt demo parsing failed: {str(e)}", exc_info=True)
            raise Exception(
                f"Failed to parse FaceIt demo with demoparser2.parse_event().\n\n"
                f"Error: {str(e)}\n\n"
                f"This could be due to:\n"
                f"1. Demo file is corrupted or incomplete\n"
                f"2. Demo is from an unsupported CS2 version\n"
                f"3. Demo file is actually from CS:GO (not CS2)\n\n"
                f"Please try:\n"
                f"- A different FaceIt demo\n"
                f"- A more recent demo (last 30 days)\n"
                f"- Updating demoparser2: pip install --upgrade demoparser2"
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

    def _extract_faceit_player_stats(self, demo_data: Dict, kills_df) -> List[PlayerStats]:
        """Extract player stats from FaceIt demo data"""
        try:
            kills_data = demo_data.get("kills", [])

            if len(kills_data) == 0:
                return []

            # Log all available column names to understand the data structure
            logger.info(f"Total columns in kills DataFrame: {len(kills_df.columns)}")

            # Find columns that might contain player names
            all_cols = list(kills_df.columns)
            name_related = [col for col in all_cols if 'name' in col.lower()]
            player_related = [col for col in all_cols if 'player' in col.lower()]
            attacker_related = [col for col in all_cols if 'attacker' in col.lower()]
            victim_related = [col for col in all_cols if 'victim' in col.lower() or 'user' in col.lower()]

            logger.info(f"Name-related columns: {name_related}")
            logger.info(f"Player-related columns: {player_related}")
            logger.info(f"Attacker-related columns: {attacker_related}")
            logger.info(f"Victim-related columns: {victim_related}")

            player_stats_map: Dict[str, Dict] = {}

            for kill in kills_data:
                # Try to find attacker and victim names from available fields
                # Start with most likely field names
                attacker_name = None
                victim_name = None

                # Try different field name combinations
                for field in name_related + attacker_related:
                    if 'attacker' in field.lower() and kill.get(field):
                        attacker_name = str(kill[field])
                        break

                for field in name_related + victim_related:
                    if ('victim' in field.lower() or 'user' in field.lower()) and kill.get(field):
                        victim_name = str(kill[field])
                        break

                # Fallback to any field with 'name'
                if not attacker_name:
                    for field in name_related:
                        if kill.get(field) and 'attacker' not in field.lower() and 'victim' not in field.lower():
                            attacker_name = str(kill[field])
                            break

                if not attacker_name:
                    attacker_name = "Unknown"
                if not victim_name:
                    victim_name = "Unknown"

                # Check for headshot
                headshot_fields = [col for col in all_cols if 'headshot' in col.lower()]
                is_headshot = False
                for field in headshot_fields:
                    if kill.get(field):
                        is_headshot = bool(kill[field])
                        break

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

            logger.info(f"Extracted stats for {len(player_stats_list)} players")
            for stat in player_stats_list[:5]:  # Log top 5
                logger.info(f"  {stat.name}: {stat.kills}K / {stat.deaths}D")

            return player_stats_list

        except Exception as e:
            logger.error(f"Error extracting FaceIt player stats: {e}", exc_info=True)
            return []

    def get_kills_data(self, demo_data: Dict) -> List[Dict]:
        """Get kills data from parsed FaceIt demo"""
        return demo_data.get("kills", [])
