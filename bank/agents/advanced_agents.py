"""Advanced strategic agents for BANK! dice game.

These agents implement sophisticated strategies designed to challenge
learning algorithms and provide tough competition during training.
"""

from __future__ import annotations

from bank.agents.base import Action, Agent, Observation


class LeaderPlusBaseAgent(Agent):
    def on_new_round(self, observation: Observation) -> None:
        """Call this at the start of each round to handle lost-lead state if needed."""
        my_id = observation["player_id"]
        my_score = observation["player_score"]
        all_scores = observation["all_player_scores"]
        max_opponent = max(
            [score for pid, score in all_scores.items() if pid != my_id],
            default=0,
        )
        is_leader = my_score > max_opponent
        if not is_leader and self._was_leader:
            self._wait_counter = self.plus_n
            self._was_leader = False

    """Base class for LeaderPlusN agents with correct leader protocol and wait logic."""

    def __init__(self, player_id: int, plus_n: int, name: str | None = None) -> None:
        super().__init__(player_id, name or f"LeaderPlus{plus_n}-{player_id}")
        self.plus_n = plus_n
        self._was_leader = False
        self._wait_counter = 0
        self._last_roll_count = None

    def act(self, observation: Observation) -> Action:
        # If this is the first act() call of a new round, check for lost-lead state
        if observation["roll_count"] == 1:
            self.on_new_round(observation)
        if observation["roll_count"] < 3:
            return "pass"
        if not observation["can_bank"]:
            return "pass"
        my_id = observation["player_id"]
        my_score = observation["player_score"]
        bank = observation["current_bank"]
        all_scores = observation["all_player_scores"]
        max_opponent = max(
            [score for pid, score in all_scores.items() if pid != my_id],
            default=0,
        )
        is_leader = my_score > max_opponent
        will_be_leader = my_score + bank > max_opponent

        # Only decrement wait counter if a new roll has occurred AND would become leader by banking
        roll_count = observation["roll_count"]
        if self._last_roll_count is None:
            self._last_roll_count = roll_count
        if roll_count != self._last_roll_count:
            if self._wait_counter > 0 and will_be_leader:
                self._wait_counter -= 1
            self._last_roll_count = roll_count

        # If currently leading
        if is_leader:
            self._was_leader = True
            return "pass"

        # If lost the lead this turn (was leader last turn, now not)
        if not is_leader and self._was_leader:
            self._wait_counter = self.plus_n
            self._was_leader = False

        # If not leading, but would take lead by banking (only allowed if not in wait period)
        if will_be_leader:
            if self._wait_counter > 0:
                return "pass"
            self._was_leader = True
            return "bank"
        # Otherwise, just pass
        return "pass"


class LeaderOnlyAgent(LeaderPlusBaseAgent):
    def __init__(self, player_id: int, name: str | None = None) -> None:
        super().__init__(player_id, 0, name or f"LeaderOnly-{player_id}")


class LeaderPlusOneAgent(LeaderPlusBaseAgent):
    def __init__(self, player_id: int, name: str | None = None) -> None:
        super().__init__(player_id, 1, name or f"LeaderPlusOne-{player_id}")


class LeaderPlusTwoAgent(LeaderPlusBaseAgent):
    def __init__(self, player_id: int, name: str | None = None) -> None:
        super().__init__(player_id, 2, name or f"LeaderPlusTwo-{player_id}")


class LeaderPlusThreeAgent(LeaderPlusBaseAgent):
    def __init__(self, player_id: int, name: str | None = None) -> None:
        super().__init__(player_id, 3, name or f"LeaderPlusThree-{player_id}")


class LeaderPlusFourAgent(LeaderPlusBaseAgent):
    def __init__(self, player_id: int, name: str | None = None) -> None:
        super().__init__(player_id, 4, name or f"LeaderPlusFour-{player_id}")


class LeaderPlusFiveAgent(LeaderPlusBaseAgent):
    def __init__(self, player_id: int, name: str | None = None) -> None:
        super().__init__(player_id, 5, name or f"LeaderPlusFive-{player_id}")


class LeaderPlusSixAgent(LeaderPlusBaseAgent):
    def __init__(self, player_id: int, name: str | None = None) -> None:
        super().__init__(player_id, 6, name or f"LeaderPlusSix-{player_id}")


class LeaderPlusSevenAgent(LeaderPlusBaseAgent):
    def __init__(self, player_id: int, name: str | None = None) -> None:
        super().__init__(player_id, 7, name or f"LeaderPlusSeven-{player_id}")


class LeechAgent(Agent):
    """Agent that waits for others to bank, then takes one more roll.

    This 'shadow strategy' watches other players' banking behavior and
    exploits conservative players by waiting slightly longer. When most
    players have banked, it knows they found the bank value acceptable,
    so it waits one more roll for extra value.

    Strengths:
    - Exploits conservative players
    - Gets better value than other players
    - Social strategy that adapts to opponents

    Weaknesses:
    - Risks losing everything if too greedy
    - Relies on others banking first (vulnerable in aggressive games)
    - Fixed threshold may not adapt well to all situations
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        min_bank: int = 40,
        min_banked_players: int = 2,
    ) -> None:
        """Initialize LeechAgent.

        Args:
            player_id: Unique identifier for this player
            name: Optional display name for the agent
            min_bank: Minimum bank value to consider banking
            min_banked_players: Minimum number of other players who must have banked

        """
        super().__init__(player_id, name or f"Leech-{player_id}")
        self.min_bank = min_bank
        self.min_banked_players = min_banked_players

    def act(self, observation: Observation) -> Action:
        """Bank when others have banked and bank value is sufficient.

        Args:
            observation: Current game state observation

        Returns:
            "bank" if enough players banked and value is good, "pass" otherwise

        """
        # Can't bank if not allowed
        if not observation["can_bank"]:
            return "pass"

        # Bank must be worth something
        if observation["current_bank"] < self.min_bank:
            return "pass"

        # Count how many players have banked this round
        # Total players = len(all_player_scores)
        # Active players = len(active_player_ids)
        # Banked players = Total - Active
        total_players = len(observation["all_player_scores"])
        active_players = len(observation["active_player_ids"])
        num_banked = total_players - active_players

        # If enough players have banked, we bank too
        if num_banked >= self.min_banked_players:
            return "bank"

        return "pass"


class RankBasedAgent(Agent):
    """Agent that adjusts aggression based on current competitive rank.

    This agent varies its banking threshold based on whether it's winning
    or losing. When behind, it becomes more aggressive (higher threshold)
    to catch up. When leading, it becomes more conservative (lower threshold)
    to protect its lead.

    Strengths:
    - Balanced and adaptive
    - Good risk management based on game state
    - Considers competitive position

    Weaknesses:
    - Thresholds are somewhat arbitrary
    - May be too predictable
    - Doesn't adapt threshold smoothly (discrete rank levels)
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        leader_threshold: int = 40,
        middle_threshold: int = 60,
        last_threshold: int = 100,
    ) -> None:
        """Initialize RankBasedAgent.

        Args:
            player_id: Unique identifier for this player
            name: Optional display name for the agent
            leader_threshold: Bank threshold when in 1st place
            middle_threshold: Bank threshold when in middle ranks
            last_threshold: Bank threshold when in last place

        """
        super().__init__(player_id, name or f"RankBased-{player_id}")
        self.leader_threshold = leader_threshold
        self.middle_threshold = middle_threshold
        self.last_threshold = last_threshold

    def act(self, observation: Observation) -> Action:
        """Bank based on rank-adjusted threshold.

        Args:
            observation: Current game state observation

        Returns:
            "bank" if bank value exceeds rank-based threshold, "pass" otherwise

        """
        # Can't bank if not allowed
        if not observation["can_bank"]:
            return "pass"

        # Calculate current rank (1 = first place, higher = worse)
        my_score = observation["player_score"]
        all_scores = observation["all_player_scores"]

        # Count how many players have higher scores
        rank = 1 + sum(1 for score in all_scores.values() if score > my_score)

        # Determine number of players
        num_players = len(all_scores)

        # Set threshold based on rank
        if rank == 1:
            # Leading - be conservative
            threshold = self.leader_threshold
        elif rank == num_players:
            # Last place - be aggressive
            threshold = self.last_threshold
        else:
            # Middle - balanced
            threshold = self.middle_threshold

        # Bank if current bank meets or exceeds threshold
        if observation["current_bank"] >= threshold:
            return "bank"

        return "pass"
