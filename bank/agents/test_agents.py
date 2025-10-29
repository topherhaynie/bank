"""Simple test agents for BANK! game.

These agents implement basic strategies useful for testing and baselines.
"""

from bank.agents.base import Action, Agent, Observation


class AlwaysPassAgent(Agent):
    """An agent that always passes (never banks)."""

    def act(self, observation: Observation) -> Action:
        """Always return 'pass'.

        Args:
            observation: Current game state observation

        Returns:
            Always returns "pass"

        """
        return "pass"


class AlwaysBankAgent(Agent):
    """An agent that always tries to bank when possible."""

    def act(self, observation: Observation) -> Action:
        """Always return 'bank' if able.

        Args:
            observation: Current game state observation

        Returns:
            "bank" if can_bank is True, otherwise "pass"

        """
        return "bank" if observation["can_bank"] else "pass"


class ThresholdAgent(Agent):
    """An agent that banks when the bank reaches a threshold."""

    def __init__(self, player_id: int, threshold: int = 50, name: str | None = None) -> None:
        """Initialize a threshold-based agent.

        Args:
            player_id: Unique identifier for this agent
            threshold: Bank value at which to bank
            name: Optional name for the agent

        """
        super().__init__(player_id, name)
        self.threshold = threshold

    def act(self, observation: Observation) -> Action:
        """Bank if current bank meets or exceeds threshold.

        Args:
            observation: Current game state observation

        Returns:
            "bank" if can bank and bank >= threshold, otherwise "pass"

        """
        if observation["can_bank"] and observation["current_bank"] >= self.threshold:
            return "bank"
        return "pass"
