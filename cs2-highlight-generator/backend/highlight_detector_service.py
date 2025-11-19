"""
Highlight Detector Service
Similar to a @Service class in Spring Boot

This service analyzes parsed demo data and identifies highlight moments
(aces, clutches, multi-kills, etc.)
"""

import logging
from typing import List, Dict, Any
from collections import defaultdict

from models import HighlightMoment, HighlightType
from config import MIN_MULTIKILL_KILLS, MULTIKILL_TIME_WINDOW, MIN_HIGH_DAMAGE

logger = logging.getLogger(__name__)


class HighlightDetectorService:
    """
    Service for detecting highlights in CS2 demos

    In Java:
    @Service
    public class HighlightDetectorService {
        public List<HighlightMoment> detectHighlights(Map demoData) { ... }
    }
    """

    def __init__(self):
        """Constructor"""
        logger.info("HighlightDetectorService initialized")

    def _get_field_value(self, data: Dict, field_names: List[str], default=None):
        """
        Try multiple possible field names and return the first non-None value

        Args:
            data: Dictionary to search
            field_names: List of possible field names to try
            default: Default value if none found

        Returns:
            First non-None value found, or default
        """
        for field in field_names:
            value = data.get(field)
            if value is not None:
                return value
        return default

    def detect_highlights(
        self,
        rounds_data: List[Dict],
        kills_data: List[Dict]
    ) -> List[HighlightMoment]:
        """
        Main method to detect all highlights in a demo

        In Java:
        public List<HighlightMoment> detectHighlights(
            List<Map> roundsData,
            List<Map> killsData
        )

        Args:
            rounds_data: List of round data from demo parser
            kills_data: List of kill events from demo parser

        Returns:
            List of detected highlight moments
        """
        logger.info("Starting highlight detection...")

        highlights: List[HighlightMoment] = []

        # Detect different types of highlights
        highlights.extend(self._detect_aces(rounds_data, kills_data))
        highlights.extend(self._detect_multikills(rounds_data, kills_data))
        highlights.extend(self._detect_clutches(rounds_data))
        highlights.extend(self._detect_high_damage_rounds(rounds_data))

        # Sort highlights by round number, then by start tick
        # In Java: highlights.sort(Comparator.comparing(HighlightMoment::getRoundNumber)
        #                                     .thenComparing(HighlightMoment::getStartTick));
        highlights.sort(key=lambda h: (h.round_number, h.start_tick))

        logger.info(f"Detected {len(highlights)} highlights")
        return highlights

    def _detect_aces(
        self,
        rounds_data: List[Dict],
        kills_data: List[Dict]
    ) -> List[HighlightMoment]:
        """
        Detect ACE moments (5 kills in a single round by one player)

        Private method (like private in Java)

        Args:
            rounds_data: Round data
            kills_data: Kill events

        Returns:
            List of ACE highlights
        """
        aces: List[HighlightMoment] = []

        # Group kills by round number
        # In Java: Map<Integer, List<Map>> killsByRound = new HashMap<>();
        kills_by_round: Dict[int, List[Dict]] = defaultdict(list)

        for kill in kills_data:
            # Try multiple possible field names for round number
            # Different parsers use different field names
            round_num = self._get_field_value(
                kill,
                ["round", "round_num", "total_rounds_played"],
                default=1  # Default to round 1 if no round data (model requires >= 1)
            )
            # Handle None values or 0 (model validation requires round_number >= 1)
            if round_num is None or round_num == 0:
                round_num = 1
            kills_by_round[int(round_num)].append(kill)

        # Debug logging for FaceIt demos
        logger.debug(f"Grouped {len(kills_data)} kills into {len(kills_by_round)} rounds")
        if kills_data and len(kills_data) > 0:
            sample_fields = list(kills_data[0].keys())
            logger.debug(f"Sample kill fields: {sample_fields[:10]}...")  # First 10 fields
            # Check for critical fields
            has_attacker_name = any("attacker" in str(k).lower() and "name" in str(k).lower() for k in sample_fields)
            has_tick = any("tick" in str(k).lower() for k in sample_fields)
            logger.debug(f"Has attacker_name-like field: {has_attacker_name}, has tick field: {has_tick}")

        # Check each round for aces
        for round_num, round_kills in kills_by_round.items():
            # Count kills per player in this round
            # In Java: Map<String, Integer> killsPerPlayer = new HashMap<>();
            kills_per_player: Dict[str, int] = defaultdict(int)

            for kill in round_kills:
                # Try multiple possible field names for attacker
                attacker = self._get_field_value(
                    kill,
                    ["attacker_name", "attacker", "killer_name", "killer"],
                    default=""
                )
                if attacker:  # Ignore environment kills
                    kills_per_player[str(attacker)] += 1

            # Find players with 5 kills (ACE)
            for player_name, kill_count in kills_per_player.items():
                if kill_count == 5:
                    # This is an ACE!
                    # Get the kills for this player in this round
                    player_kills = [
                        k for k in round_kills
                        if self._get_field_value(k, ["attacker_name", "attacker", "killer_name", "killer"], "") == player_name
                    ]

                    # Sort by tick to get chronological order
                    player_kills.sort(key=lambda k: self._get_field_value(k, ["tick", "server_tick", "game_tick"], 0))

                    # Get first and last kill ticks
                    start_tick = self._get_field_value(player_kills[0], ["tick", "server_tick", "game_tick"], 0)
                    end_tick = self._get_field_value(player_kills[-1], ["tick", "server_tick", "game_tick"], 0)

                    # Add some padding (5 seconds before first kill, 3 seconds after last)
                    # 128 ticks per second in CS2
                    TICKS_PER_SECOND = 128
                    start_tick = max(0, start_tick - (5 * TICKS_PER_SECOND))
                    end_tick = end_tick + (3 * TICKS_PER_SECOND)

                    # Calculate time in seconds (for display)
                    start_time = start_tick / TICKS_PER_SECOND
                    end_time = end_tick / TICKS_PER_SECOND

                    # Get weapons used
                    weapons = list(set([
                        self._get_field_value(k, ["weapon", "weapon_name", "weapon_type"], "Unknown")
                        for k in player_kills
                    ]))

                    # Calculate total damage
                    total_damage = sum([
                        self._get_field_value(k, ["attacker_damage", "damage", "dmg_health"], 0)
                        for k in player_kills
                    ])

                    # Create highlight moment
                    ace = HighlightMoment(
                        type=HighlightType.ACE,
                        round_number=round_num,
                        start_tick=start_tick,
                        end_tick=end_tick,
                        start_time=round(start_time, 2),
                        end_time=round(end_time, 2),
                        player_name=player_name,
                        kills=5,
                        damage=total_damage,
                        is_clutch=False,  # TODO: Detect if it was a clutch ace
                        weapons_used=weapons,
                        description=f"{player_name} ACE with {', '.join(weapons)} in round {round_num}"
                    )

                    aces.append(ace)
                    logger.info(f"Detected ACE: {ace.description}")

        return aces

    def _detect_multikills(
        self,
        rounds_data: List[Dict],
        kills_data: List[Dict]
    ) -> List[HighlightMoment]:
        """
        Detect multi-kill moments (3K, 4K within a short time window)

        Args:
            rounds_data: Round data
            kills_data: Kill events

        Returns:
            List of multi-kill highlights
        """
        multikills: List[HighlightMoment] = []

        # Group kills by round
        kills_by_round: Dict[int, List[Dict]] = defaultdict(list)
        for kill in kills_data:
            # Try multiple possible field names for round number
            round_num = self._get_field_value(
                kill,
                ["round", "round_num", "total_rounds_played"],
                default=1  # Default to round 1 if no round data (model requires >= 1)
            )
            # Handle None values or 0 (model validation requires round_number >= 1)
            if round_num is None or round_num == 0:
                round_num = 1
            kills_by_round[int(round_num)].append(kill)

        # Check each round
        for round_num, round_kills in kills_by_round.items():
            # Group kills by player
            kills_by_player: Dict[str, List[Dict]] = defaultdict(list)
            for kill in round_kills:
                attacker = self._get_field_value(
                    kill,
                    ["attacker_name", "attacker", "killer_name", "killer"],
                    default=""
                )
                if attacker:
                    kills_by_player[str(attacker)].append(kill)

            # Check each player's kills
            for player_name, player_kills in kills_by_player.items():
                # Skip if already detected as ACE (5 kills)
                if len(player_kills) == 5:
                    continue

                # Sort kills by tick
                player_kills.sort(key=lambda k: self._get_field_value(k, ["tick", "server_tick", "game_tick"], 0))

                # Find sequences of quick kills
                # A "multi-kill" is MIN_MULTIKILL_KILLS kills within MULTIKILL_TIME_WINDOW seconds
                TICKS_PER_SECOND = 128

                for i in range(len(player_kills)):
                    # Try to find a sequence starting at position i
                    sequence = [player_kills[i]]
                    start_tick = self._get_field_value(player_kills[i], ["tick", "server_tick", "game_tick"], 0)

                    for j in range(i + 1, len(player_kills)):
                        current_tick = self._get_field_value(player_kills[j], ["tick", "server_tick", "game_tick"], 0)
                        time_diff = (current_tick - start_tick) / TICKS_PER_SECOND

                        if time_diff <= MULTIKILL_TIME_WINDOW:
                            sequence.append(player_kills[j])
                        else:
                            break

                    # Check if we have a multi-kill
                    kill_count = len(sequence)
                    if kill_count >= MIN_MULTIKILL_KILLS:
                        # Determine type (3K or 4K)
                        if kill_count == 4:
                            highlight_type = HighlightType.QUADRA_KILL
                        elif kill_count == 3:
                            highlight_type = HighlightType.TRIPLE_KILL
                        else:
                            continue  # Skip if not 3 or 4

                        # Get ticks
                        start_tick = self._get_field_value(sequence[0], ["tick", "server_tick", "game_tick"], 0)
                        end_tick = self._get_field_value(sequence[-1], ["tick", "server_tick", "game_tick"], 0)

                        # Add padding
                        start_tick = max(0, start_tick - (5 * TICKS_PER_SECOND))
                        end_tick = end_tick + (3 * TICKS_PER_SECOND)

                        # Calculate times
                        start_time = start_tick / TICKS_PER_SECOND
                        end_time = end_tick / TICKS_PER_SECOND

                        # Get weapons
                        weapons = list(set([self._get_field_value(k, ["weapon", "weapon_name", "weapon_type"], "Unknown") for k in sequence]))

                        # Total damage
                        total_damage = sum([self._get_field_value(k, ["attacker_damage", "damage", "dmg_health"], 0) for k in sequence])

                        # Create highlight
                        multikill = HighlightMoment(
                            type=highlight_type,
                            round_number=round_num,
                            start_tick=start_tick,
                            end_tick=end_tick,
                            start_time=round(start_time, 2),
                            end_time=round(end_time, 2),
                            player_name=player_name,
                            kills=kill_count,
                            damage=total_damage,
                            is_clutch=False,
                            weapons_used=weapons,
                            description=f"{player_name} {kill_count}K with {', '.join(weapons)} in round {round_num}"
                        )

                        multikills.append(multikill)
                        logger.info(f"Detected {kill_count}K: {multikill.description}")

                        # Don't look for overlapping sequences
                        break

        return multikills

    def _detect_clutches(self, rounds_data: List[Dict]) -> List[HighlightMoment]:
        """
        Detect clutch moments (1vX situations that were won)

        Note: This is more complex and requires analyzing player counts
        For the MVP, we'll implement a simplified version

        Args:
            rounds_data: Round data

        Returns:
            List of clutch highlights
        """
        clutches: List[HighlightMoment] = []

        # TODO: Implement clutch detection
        # This requires analyzing:
        # 1. When did it become a 1vX situation?
        # 2. Did the lone player win the round?
        # 3. How many enemies were alive?
        #
        # For MVP, we'll skip this and add it in Phase 2

        logger.debug("Clutch detection not yet implemented")
        return clutches

    def _detect_high_damage_rounds(self, rounds_data: List[Dict]) -> List[HighlightMoment]:
        """
        Detect rounds where a player dealt exceptionally high damage

        Args:
            rounds_data: Round data

        Returns:
            List of high damage round highlights
        """
        high_damage_rounds: List[HighlightMoment] = []

        # TODO: Implement high damage detection
        # This requires analyzing damage data per round per player
        # For MVP, we'll skip this

        logger.debug("High damage round detection not yet implemented")
        return high_damage_rounds
