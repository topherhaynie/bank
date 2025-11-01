"""Advanced threshold agents for BANK! dice game.

Implements threshold agents for 300, 350, 400, 450, 500 with adaptive protocols:
- Bank at threshold if not behind.
- If behind after half the game, switch to leader protocol (wait for leadership).
- In last 3 rounds, if leading, only bank if overtaken (bank to retake lead).
"""

from __future__ import annotations

from bank.agents.base import Action, Agent, Observation


class AdaptiveThresholdAgent(Agent):
    """Threshold agent with adaptive losing and leader protocols.

    - Banks at threshold if not behind.
    - If behind after half the game, switches to leader protocol (bank only if it would take the lead).
    - In the last 3 rounds, if leading, only banks if overtaken (bank to retake lead).
    """

    def __init__(self, player_id: int, threshold: int, name: str | None = None) -> None:
        """Initialize the adaptive threshold agent.

        Args:
            player_id: Unique identifier for this player
            threshold: Bank value at which to bank
            name: Optional name for display purposes

        """
        super().__init__(player_id, name or f"Threshold-{threshold}")
        self.threshold = threshold

    def act(self, observation: Observation) -> Action:
        """Decide whether to bank based on adaptive threshold and game context.

        Args:
            observation: Current game state observation

        Returns:
            "bank" or "pass"

        """
        if not observation["can_bank"]:
            return "pass"

        my_score = observation["player_score"]
        all_scores = observation["all_player_scores"]
        round_num = observation.get("round_number", 1)
        total_rounds = observation.get("total_rounds", 10)
        bank = observation["current_bank"]
        my_id = observation["player_id"]
        max_opponent = max([score for pid, score in all_scores.items() if pid != my_id], default=0)
        is_leader = my_score > max_opponent
        LAST_ROUNDS = 3
        is_last_3 = total_rounds - round_num < LAST_ROUNDS
        is_last = round_num == total_rounds
        half_game = round_num > total_rounds // 2
        behind = my_score < max_opponent

        # Last 3 rounds: if leading, only bank if overtaken (bank to retake lead)
        if is_last_3 or is_last:
            if is_leader:
                if my_score + bank > max_opponent:
                    return "bank"
                return "pass"
            # If not leader, try to take lead
            if my_score + bank > max_opponent:
                return "bank"
            return "pass"

        # If behind after half the game, use leader protocol
        if half_game and behind:
            if my_score + bank > max_opponent:
                return "bank"
            return "pass"

        # Normal threshold protocol
        if bank >= self.threshold:
            return "bank"
        return "pass"


# Clean, unique, and correct factory functions for each threshold
def threshold_250_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-250 agent."""
    return AdaptiveThresholdAgent(player_id, 250, name or "Threshold-250")


def threshold_275_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-275 agent."""
    return AdaptiveThresholdAgent(player_id, 275, name or "Threshold-275")


def threshold_300_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-300 agent."""
    return AdaptiveThresholdAgent(player_id, 300, name or "Threshold-300")


def threshold_325_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-325 agent."""
    return AdaptiveThresholdAgent(player_id, 325, name or "Threshold-325")


def threshold_350_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-350 agent."""
    return AdaptiveThresholdAgent(player_id, 350, name or "Threshold-350")


def threshold_375_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-375 agent."""
    return AdaptiveThresholdAgent(player_id, 375, name or "Threshold-375")


def threshold_400_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-400 agent."""
    return AdaptiveThresholdAgent(player_id, 400, name or "Threshold-400")


def threshold_425_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-425 agent."""
    return AdaptiveThresholdAgent(player_id, 425, name or "Threshold-425")


def threshold_450_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-450 agent."""
    return AdaptiveThresholdAgent(player_id, 450, name or "Threshold-450")


def threshold_475_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-475 agent."""
    return AdaptiveThresholdAgent(player_id, 475, name or "Threshold-475")


def threshold_500_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-500 agent."""
    return AdaptiveThresholdAgent(player_id, 500, name or "Threshold-500")


def threshold_550_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-550 agent."""
    return AdaptiveThresholdAgent(player_id, 550, name or "Threshold-550")


def threshold_600_agent(player_id: int, name: str | None = None) -> AdaptiveThresholdAgent:
    """Return Threshold-600 agent."""
    return AdaptiveThresholdAgent(player_id, 600, name or "Threshold-600")
