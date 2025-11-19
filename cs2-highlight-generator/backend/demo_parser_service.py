"""
Demo Parser Service
Similar to a @Service class in Spring Boot

This service handles parsing CS2 demo files and extracting data.
Think of this as a Service layer in Java that encapsulates business logic.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

# awpy is the CS2 demo parsing library (no Java equivalent)
# It reads .dem files and extracts all game data
from awpy import Demo

from models import MatchInfo, PlayerStats

# Set up logging (similar to Log4j in Java)
logger = logging.getLogger(__name__)


class DemoParserService:
    """
    Service class for parsing CS2 demo files

    In Java, this would be:
    @Service
    public class DemoParserService {
        public DemoAnalysisResult parseDemo(File demoFile) { ... }
    }

    This class is stateless and thread-safe (like a Spring singleton bean)
    """

    def __init__(self):
        """
        Constructor
        In Java: public DemoParserService() { ... }
        """
        logger.info("DemoParserService initialized")

    def parse_demo_file(self, demo_file_path: Path) -> Dict[str, Any]:
        """
        Parse a CS2 demo file and extract all relevant data

        Args:
            demo_file_path: Path to the .dem file

        Returns:
            Dictionary containing parsed data (rounds, kills, players, etc.)

        Raises:
            Exception: If demo parsing fails

        In Java:
        public Map<String, Object> parseDemoFile(Path demoFilePath) throws Exception
        """
        logger.info(f"Starting to parse demo file: {demo_file_path}")
        start_time = time.time()

        try:
            # Validate file exists
            if not demo_file_path.exists():
                raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

            # Initialize the Demo object (awpy 2.0+ API)
            # This is the main class from the awpy library
            logger.info("Parsing demo... this may take 10-30 seconds")

            # Try parsing with error handling
            demo_data = None
            parse_error = None

            try:
                # Method 1: Standard parsing (works for most CS2 demos)
                demo = Demo(
                    path=demo_file_path,  # Path to demo file
                    tickrate=128,  # 128 ticks/second in CS2
                    verbose=False  # Don't print debug messages
                )

                demo.parse()  # Parse all data
                demo.parse_header()  # Parse header info (map name, etc.)

                # Build a dictionary structure similar to old API for compatibility
                # In awpy 2.0+, data is accessed as attributes (demo.kills, demo.damages, etc.)
                demo_data = {
                    "header": {
                        "map_name": getattr(demo, 'map_name', 'Unknown'),
                    },
                    "kills": demo.kills if demo.kills is not None else [],
                    "damages": demo.damages if demo.damages is not None else [],
                    "bomb": demo.bomb if demo.bomb is not None else [],
                    "rounds": []  # awpy 2.0+ has different round structure
                }

            except KeyError as ke:
                # Specific handling for missing event errors
                parse_error = str(ke)
                if "round_officially_ended" in parse_error:
                    logger.warning(f"Demo missing 'round_officially_ended' event (common with FaceIt demos)")
                    logger.info("Attempting to extract kills data without round parsing...")

                    # Method 2: FaceIt/Custom Server Workaround
                    # The error occurs AFTER events are parsed, so we can access them
                    try:
                        # Check if demo object exists and has events/kills data
                        if hasattr(demo, 'kills') and demo.kills is not None:
                            logger.info(f"Found {len(demo.kills)} kills in partially parsed demo")
                            demo_data = {
                                "header": {
                                    "map_name": getattr(demo, 'map_name', 'Unknown'),
                                },
                                "kills": demo.kills,
                                "damages": demo.damages if hasattr(demo, 'damages') and demo.damages is not None else [],
                                "bomb": demo.bomb if hasattr(demo, 'bomb') and demo.bomb is not None else [],
                                "rounds": []  # FaceIt demos don't have standard round data
                            }
                            logger.info("✓ Successfully extracted kills from FaceIt demo (rounds skipped)")
                        else:
                            # If that didn't work, try re-parsing with custom approach
                            raise ValueError("No kills data found in partial parse")

                    except Exception as e2:
                        logger.warning(f"Could not use partial data: {e2}")
                        logger.info("Trying custom parsing for FaceIt demos...")

                        # Method 3: Parse events manually
                        try:
                            # Create new demo instance
                            demo_alt = Demo(
                                path=demo_file_path,
                                tickrate=128,
                                verbose=True  # Enable verbose for debugging
                            )

                            # Parse header and events only (don't call parse() which triggers round parsing)
                            demo_alt.parse_header()

                            # Try to access the parser directly to get just kills
                            # In awpy 2.0+, parsing happens in parse() which we can't call
                            # So we'll try to get kills from the events if they exist
                            try:
                                # Attempt to trigger event parsing without round parsing
                                # This is a hack - we call parse but catch the round error
                                demo_alt.parse()
                            except KeyError:
                                # Expected - round parsing will fail, but events should be parsed
                                pass

                            # Now try to get data from the demo object
                            if hasattr(demo_alt, 'kills') and demo_alt.kills is not None:
                                demo_data = {
                                    "header": {
                                        "map_name": getattr(demo_alt, 'map_name', 'Unknown'),
                                    },
                                    "kills": demo_alt.kills,
                                    "damages": demo_alt.damages if hasattr(demo_alt, 'damages') else [],
                                    "bomb": [],
                                    "rounds": []
                                }
                                logger.info(f"✓ Extracted {len(demo_alt.kills)} kills from FaceIt demo")
                            else:
                                raise ValueError("Failed to extract any data")

                        except Exception as e3:
                            logger.error(f"All FaceIt parsing methods failed: {e3}")
                            raise Exception(
                                f"Failed to parse FaceIt demo.\n\n"
                                f"**This is a known issue with FaceIt CS2 demos.**\n\n"
                                f"FaceIt servers use a custom configuration that is not fully compatible "
                                f"with the awpy parsing library (missing 'round_officially_ended' event).\n\n"
                                f"**Workarounds:**\n"
                                f"1. Try a demo from official CS2 matchmaking (Watch → Your Matches)\n"
                                f"2. Wait for awpy library update to support FaceIt demos\n"
                                f"3. The developer needs to implement custom FaceIt demo parsing\n\n"
                                f"Original error: {parse_error}\n\n"
                                f"Sorry, FaceIt demo support is limited in the current version."
                            )
                else:
                    raise

            except Exception as e:
                parse_error = str(e)
                logger.warning(f"Standard parsing failed: {e}")

                # Method 3: Last resort - try with different settings
                try:
                    logger.info("Retrying with alternative settings...")
                    demo = Demo(
                        path=demo_file_path,
                        tickrate=64,  # Lower tickrate
                        verbose=True  # Enable verbose to see what's happening
                    )

                    # Parse header first (less likely to fail)
                    demo.parse_header()

                    # Then try parsing data
                    demo.parse()

                    demo_data = {
                        "header": {
                            "map_name": getattr(demo, 'map_name', 'Unknown'),
                        },
                        "kills": demo.kills if demo.kills is not None else [],
                        "damages": demo.damages if demo.damages is not None else [],
                        "bomb": demo.bomb if demo.bomb is not None else [],
                        "rounds": []
                    }

                except Exception as e2:
                    logger.error(f"Alternative parsing also failed: {e2}")
                    # Raise detailed error
                    raise Exception(
                        f"Failed to parse demo file. Possible causes:\n\n"
                        f"1. **Demo is from CS:GO (not CS2)**: This tool only supports CS2 demos\n"
                        f"2. **Corrupted or incomplete demo**: Try downloading again\n"
                        f"3. **Unsupported CS2 version**: Try a more recent demo\n"
                        f"4. **Outdated awpy library**: Run this command:\n"
                        f"   pip install --upgrade awpy\n\n"
                        f"Original error: {parse_error}\n\n"
                        f"Suggestions:\n"
                        f"- Download a fresh demo from a recent competitive match\n"
                        f"- Make sure it's CS2, not CS:GO\n"
                        f"- Try a different demo file to isolate the issue"
                    )

            if demo_data is None:
                raise Exception("Demo parsing returned no data")

            elapsed = time.time() - start_time
            logger.info(f"Demo parsed successfully in {elapsed:.2f} seconds")

            # Extract basic match information
            match_info = self._extract_match_info(demo_data)

            # Extract player statistics
            player_stats = self._extract_player_stats(demo_data)

            return {
                "raw_data": demo_data,  # Full parsed data
                "match_info": match_info,
                "player_stats": player_stats,
                "parsing_time": elapsed
            }

        except Exception as e:
            logger.error(f"Error parsing demo file: {str(e)}", exc_info=True)
            raise Exception(f"Failed to parse demo: {str(e)}")

    def _extract_match_info(self, demo_data: Dict) -> MatchInfo:
        """
        Extract basic match information from parsed demo data

        Private method (indicated by _ prefix, like private in Java)
        In Java: private MatchInfo extractMatchInfo(Map<String, Object> demoData)

        Args:
            demo_data: Parsed demo data from awpy

        Returns:
            MatchInfo object with match metadata
        """
        try:
            # Get the map name from the demo header
            # Header contains metadata like map name, server, etc.
            header = demo_data.get("header", {})
            map_name = header.get("map_name", "Unknown")

            # In awpy 2.0+, we don't have easy access to round-by-round data in the same format
            # We'll estimate based on kills data instead
            kills = demo_data.get("kills", [])

            # Estimate rounds from kills data (rough approximation)
            # In a typical CS2 match, there are 10-30+ rounds
            total_rounds = len(kills) // 3 if len(kills) > 0 else 0  # Rough estimate

            # For MVP, we'll use placeholder values for scores
            # In a full implementation, we'd need to parse round-specific data
            team_1_score = 0
            team_2_score = 0

            # Estimate duration (placeholder - typically 30-45 minutes for a full match)
            duration_minutes = 30.0  # Placeholder value

            return MatchInfo(
                map_name=map_name,
                total_rounds=total_rounds,
                team_1_score=team_1_score,
                team_2_score=team_2_score,
                duration_minutes=duration_minutes
            )

        except Exception as e:
            logger.warning(f"Error extracting match info: {e}")
            # Return default values if extraction fails
            return MatchInfo(
                map_name="Unknown",
                total_rounds=0,
                team_1_score=0,
                team_2_score=0,
                duration_minutes=0.0
            )

    def _extract_player_stats(self, demo_data: Dict) -> List[PlayerStats]:
        """
        Extract player statistics from parsed demo data

        In Java: private List<PlayerStats> extractPlayerStats(Map demoData)

        Args:
            demo_data: Parsed demo data

        Returns:
            List of PlayerStats objects
        """
        try:
            # Player stats are aggregated across all rounds
            # We'll use the kills data to calculate stats
            kills_data = demo_data.get("kills", [])

            # Dictionary to store stats per player
            # In Java: Map<String, PlayerStatsBuilder> playerStatsMap = new HashMap<>();
            player_stats_map: Dict[str, Dict] = {}

            # Process each kill event
            for kill in kills_data:
                attacker_name = kill.get("attacker_name", "Unknown")
                victim_name = kill.get("victim_name", "Unknown")
                is_headshot = kill.get("is_headshot", False)

                # Initialize attacker stats if not exists
                if attacker_name not in player_stats_map:
                    player_stats_map[attacker_name] = {
                        "kills": 0,
                        "deaths": 0,
                        "headshots": 0,
                        "total_damage": 0
                    }

                # Initialize victim stats if not exists
                if victim_name not in player_stats_map:
                    player_stats_map[victim_name] = {
                        "kills": 0,
                        "deaths": 0,
                        "headshots": 0,
                        "total_damage": 0
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
                deaths = stats["deaths"]
                headshots = stats["headshots"]

                # Calculate headshot percentage
                hs_percentage = (headshots / kills * 100) if kills > 0 else 0.0

                # Note: ADR calculation would require damage data
                # For now, we'll set it to 0
                adr = 0.0  # TODO: Calculate from damage data

                player_stats_list.append(PlayerStats(
                    name=player_name,
                    kills=kills,
                    deaths=deaths,
                    assists=0,  # TODO: Calculate assists
                    headshot_percentage=round(hs_percentage, 2),
                    adr=adr
                ))

            # Sort by kills (descending)
            # In Java: Collections.sort(playerStatsList, Comparator.comparingInt(PlayerStats::getKills).reversed());
            player_stats_list.sort(key=lambda p: p.kills, reverse=True)

            return player_stats_list

        except Exception as e:
            logger.warning(f"Error extracting player stats: {e}")
            return []

    def get_rounds_data(self, demo_data: Dict) -> List[Dict]:
        """
        Get detailed round data from parsed demo

        Public method to access rounds data
        In Java: public List<Map<String, Object>> getRoundsData(Map demoData)

        Args:
            demo_data: Parsed demo data

        Returns:
            List of round data dictionaries
        """
        return demo_data.get("rounds", [])

    def get_kills_data(self, demo_data: Dict) -> List[Dict]:
        """
        Get all kills from parsed demo

        In Java: public List<Map<String, Object>> getKillsData(Map demoData)

        Args:
            demo_data: Parsed demo data

        Returns:
            List of kill event dictionaries
        """
        return demo_data.get("kills", [])
