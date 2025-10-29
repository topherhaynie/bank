"""Random Agent for BANK! dice game.

A simple agent that randomly decides whether to bank or pass.
Useful for testing, baselines, and as a reference implementation.
"""

from __future__ import annotations

import random

from bank.agents.base import Action, Agent, Observation


class RandomAgent(Agent):
    """Agent that randomly chooses to bank or pass.

    This agent makes decisions by flipping a coin (50/50 chance) each time
    it's asked to act. It respects the can_bank constraint and will only
    pass if banking is not allowed.

    Useful as:
    - A baseline for comparing more sophisticated strategies
    - A testing tool for the game engine
    - A reference implementation of the Agent interface

    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        seed: int | None = None,
        bank_probability: float = 0.5,
    ) -> None:
        """Initialize the random agent.

        Args:
            player_id: Unique identifier for this player (0-based)
            name: Optional name for display purposes
            seed: Optional random seed for reproducibility
            bank_probability: Probability of banking when allowed (0.0 to 1.0)

        """
        super().__init__(player_id, name or f"RandomBot-{player_id}")
        self.rng = random.Random(seed)
        self.bank_probability = max(0.0, min(1.0, bank_probability))

    def act(self, observation: Observation) -> Action:
        """Randomly decide to bank or pass.

        Args:
            observation: Current game state information

        Returns:
            "bank" with probability bank_probability if can_bank is True,
            otherwise "pass"

        """
        # Can't bank if already banked
        if not observation["can_bank"]:
            return "pass"

        # Random decision based on bank_probability
        if self.rng.random() < self.bank_probability:
            return "bank"
        return "pass"

    def reset(self) -> None:
        """Reset agent state for a new game.

        The RNG state is preserved across games for reproducibility.

        """
        # RNG maintains its state for reproducibility across games
