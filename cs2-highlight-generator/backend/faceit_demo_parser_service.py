"""
FaceIt Demo Parser Service
Specialized service for parsing FaceIt CS2 demos

FaceIt servers use custom configurations and don't emit standard events like
'round_officially_ended', which breaks standard awpy parsing. This service
uses alternative approaches to extract kills and highlights from FaceIt demos.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any
import time

from awpy import Demo

from models import MatchInfo, PlayerStats

logger = logging.getLogger(__name__)


class FaceItDemoParserService:
    """
    Specialized parser for FaceIt demos

    In Java:
    @Service
    public class FaceItDemoParserService {
        public DemoData parseFaceItDemo(File demoFile) { ... }
    }
    """

    def __init__(self):
        """Constructor"""
        logger.info("FaceItDemoParserService initialized")

    def parse_faceit_demo(self, demo_file_path: Path) -> Dict[str, Any]:
        """
        Parse a FaceIt CS2 demo file with custom handling

        Args:
            demo_file_path: Path to the .dem file

        Returns:
            Dictionary containing kills, damages, and basic match info

        Raises:
            Exception: If parsing fails completely
        """
        logger.info(f"Parsing FaceIt demo: {demo_file_path}")
        start_time = time.time()

        try:
            if not demo_file_path.exists():
                raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

            # Strategy 1: Parse and catch the round error, then extract what we can
            demo_data = self._parse_with_error_recovery(demo_file_path)

            if demo_data is None:
                # Strategy 2: Try alternative parsing method
                logger.info("Strategy 1 failed, trying alternative parsing...")
                demo_data = self._parse_events_only(demo_file_path)

            if demo_data is None:
                raise Exception("All FaceIt parsing strategies failed")

            elapsed = time.time() - start_time
            logger.info(f"✓ FaceIt demo parsed successfully in {elapsed:.2f} seconds")
            logger.info(f"  Found {len(demo_data.get('kills', []))} kills")

            # Extract match info
            match_info = self._extract_faceit_match_info(demo_data)

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
            raise Exception(f"Failed to parse FaceIt demo: {str(e)}")

    def _parse_with_error_recovery(self, demo_file_path: Path) -> Dict[str, Any]:
        """
        Parse demo and recover data even if round parsing fails

        The key insight: awpy parses kills BEFORE rounds, so when round parsing
        fails, kills data is already in memory. We just need to access it.
        """
        try:
            demo = Demo(path=demo_file_path, tickrate=128, verbose=False)

            # Try to parse - this will fail on rounds but hopefully parse kills first
            try:
                demo.parse()
            except (KeyError, Exception) as e:
                # Expected to fail on round parsing
                logger.info(f"Parse failed as expected (rounds): {e}")
                # But demo object should still have partial data
                pass

            # Parse header separately (usually works)
            try:
                demo.parse_header()
            except:
                pass

            # Now check what data we got
            kills = []
            damages = []
            bomb = []
            map_name = "Unknown"

            # Try to extract kills - each property access can trigger parsing, so wrap in try-except
            try:
                kills_raw = demo.kills
                logger.info(f"Kills data type: {type(kills_raw)}")

                if kills_raw is not None:
                    # Check if it's a list, DataFrame, or Polars DataFrame
                    if isinstance(kills_raw, list):
                        kills = kills_raw if len(kills_raw) > 0 else []
                        logger.info(f"Kills is a list with {len(kills)} items")
                    elif hasattr(kills_raw, 'to_dict'):
                        # Polars DataFrame or Pandas DataFrame
                        logger.info(f"Kills is a DataFrame with shape: {kills_raw.shape if hasattr(kills_raw, 'shape') else 'unknown'}")
                        try:
                            kills = kills_raw.to_dict('records')
                            logger.info(f"Converted DataFrame to {len(kills)} records")
                        except Exception as conv_err:
                            logger.warning(f"Could not convert to dict: {conv_err}")
                            kills = []
                    else:
                        logger.warning(f"Unknown kills data type: {type(kills_raw)}")
                        kills = []

                    if len(kills) > 0:
                        logger.info(f"✓ Extracted {len(kills)} kills from demo object")
                        # Log first kill to see structure
                        logger.debug(f"Sample kill: {kills[0]}")
                else:
                    logger.warning("demo.kills is None")
            except Exception as e:
                logger.warning(f"Could not access kills: {e}", exc_info=True)

            # Try to extract damages
            try:
                if demo.damages is not None:
                    if isinstance(demo.damages, list):
                        damages = demo.damages if len(demo.damages) > 0 else []
                    else:
                        try:
                            damages = demo.damages.to_dict('records') if hasattr(demo.damages, 'to_dict') else []
                        except:
                            damages = []

                    if len(damages) > 0:
                        logger.info(f"✓ Extracted {len(damages)} damage events")
            except Exception as e:
                logger.warning(f"Could not access damages: {e}")

            # Try to extract bomb events - this often fails, so we'll skip it if it does
            try:
                if demo.bomb is not None:
                    if isinstance(demo.bomb, list):
                        bomb = demo.bomb
                    else:
                        try:
                            bomb = demo.bomb.to_dict('records') if hasattr(demo.bomb, 'to_dict') else []
                        except:
                            bomb = []
            except Exception as e:
                # Bomb parsing often fails for FaceIt demos - that's okay
                logger.debug(f"Could not access bomb data (expected for FaceIt): {e}")
                bomb = []

            # Try to get map name
            try:
                if demo.map_name:
                    map_name = demo.map_name
            except:
                pass

            # Check if we got any useful data
            if len(kills) == 0:
                logger.warning("No kills found in partial parse - kills attribute is empty or not populated")
                logger.info(f"Demo object attributes: {dir(demo)}")
                return None

            return {
                "header": {"map_name": map_name},
                "kills": kills,
                "damages": damages,
                "bomb": bomb,
                "rounds": []  # FaceIt doesn't have round data
            }

        except Exception as e:
            logger.warning(f"Error recovery parsing failed: {e}", exc_info=True)
            return None

    def _parse_events_only(self, demo_file_path: Path) -> Dict[str, Any]:
        """
        Alternative: Try to parse just events without full demo parsing

        This is a backup method if the error recovery approach doesn't work.
        """
        try:
            logger.info("Attempting events-only parsing...")

            # Try with verbose mode to see what's happening
            demo = Demo(path=demo_file_path, tickrate=128, verbose=True)

            # Parse header
            demo.parse_header()
            map_name = getattr(demo, 'map_name', 'Unknown')

            # Try to manually trigger event parsing without full parse
            # This might not work in awpy 2.0+ but worth trying
            try:
                if hasattr(demo, 'parse_events'):
                    demo.parse_events()
                    logger.info("✓ Events parsed")
            except:
                pass

            # Try to parse kills from events if they exist
            try:
                if hasattr(demo, 'parse_kills'):
                    demo.parse_kills()
                    logger.info("✓ Kills parsed")
            except:
                pass

            # Check what we got
            kills = demo.kills if hasattr(demo, 'kills') and demo.kills else []
            damages = demo.damages if hasattr(demo, 'damages') and demo.damages else []

            if len(kills) > 0:
                logger.info(f"✓ Alternative parsing found {len(kills)} kills")
                return {
                    "header": {"map_name": map_name},
                    "kills": kills,
                    "damages": damages,
                    "bomb": [],
                    "rounds": []
                }

            return None

        except Exception as e:
            logger.warning(f"Events-only parsing failed: {e}")
            return None

    def _extract_faceit_match_info(self, demo_data: Dict) -> MatchInfo:
        """Extract match info from FaceIt demo data"""
        try:
            header = demo_data.get("header", {})
            map_name = header.get("map_name", "Unknown")

            kills = demo_data.get("kills", [])

            # Estimate rounds from kills (rough)
            # Average CS2 round has about 3-5 kills
            estimated_rounds = max(len(kills) // 4, 1)

            return MatchInfo(
                map_name=map_name,
                total_rounds=estimated_rounds,
                team_1_score=0,  # Can't determine from FaceIt demos
                team_2_score=0,
                duration_minutes=30.0  # Placeholder
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
                attacker_name = kill.get("attacker_name", "Unknown")
                victim_name = kill.get("victim_name", "Unknown")
                is_headshot = kill.get("is_headshot", False)

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
                    assists=0,
                    headshot_percentage=round(hs_percentage, 2),
                    adr=0.0
                ))

            # Sort by kills
            player_stats_list.sort(key=lambda p: p.kills, reverse=True)

            return player_stats_list

        except Exception as e:
            logger.warning(f"Error extracting FaceIt player stats: {e}")
            return []

    def get_kills_data(self, demo_data: Dict) -> List[Dict]:
        """Get kills data from parsed FaceIt demo"""
        return demo_data.get("kills", [])
