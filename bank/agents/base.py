"""Base Agent Interface

Defines the interface that all agents (manual, AI, etc.) must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Literal, TypedDict

from bank.game.state import GameState

# Type alias for agent actions
Action = Literal["bank", "pass"]


class Observation(TypedDict):
    """Observation dictionary provided to agents for decision-making.

    Attributes:
        round_number: Current round number (1-based)
        roll_count: Number of rolls in current round (1-based)
        current_bank: Current value in the bank
        last_roll: Tuple of (die1, die2) from most recent roll, or None
        active_player_ids: Set of player IDs still active in the round
        player_id: ID of the player receiving this observation
        player_score: Current score of the player
        can_bank: Whether the player can bank (hasn't banked yet this round)
        all_player_scores: Dict mapping player_id to their current scores

    """

    round_number: int
    roll_count: int
    current_bank: int
    last_roll: tuple[int, int] | None
    active_player_ids: set[int]
    player_id: int
    player_score: int
    can_bank: bool
    all_player_scores: dict[int, int]


class Agent(ABC):
    """Abstract base class for BANK! dice game agents.

    This is the interface for the dice-based BANK! game where agents
    make bank/pass decisions based on observations.
    """

    def __init__(self, player_id: int, name: str | None = None) -> None:
        """Initialize an agent.

        Args:
            player_id: Unique identifier for this agent/player
            name: Optional name for the agent

        """
        self.player_id = player_id
        self.name = name or f"Agent {player_id}"

    @abstractmethod
    def act(self, observation: Observation) -> Action:
        """Make a decision based on the current observation.

        Args:
            observation: Current game state observation

        Returns:
            Action: either "bank" or "pass"

        """
        ...

    def reset(self) -> None:
        """Reset the agent's internal state for a new game.

        This is called at the start of each game. Agents can override
        this if they maintain internal state that needs resetting.
        """


# Legacy interface for card-based game (kept for backward compatibility)
class BaseAgent(ABC):
    """Abstract base class for all BANK! game agents.

    All agents (human, random, rule-based, DQN, etc.) should inherit from this class.
    """

    def __init__(self, player_id: int, name: str):
        """Initialize the agent.

        Args:
            player_id: The player ID this agent controls
            name: The agent's name

        """
        self.player_id = player_id
        self.name = name

    @abstractmethod
    def select_action(self, game_state: GameState, valid_actions: list) -> tuple[str, dict[str, Any]]:
        """Select an action to take given the current game state.

        Args:
            game_state: Current game state
            valid_actions: List of valid action names

        Returns:
            Tuple of (action_name, action_parameters)

        """

    def on_game_start(self, game_state: GameState) -> None:
        """Called when a new game starts.

        Args:
            game_state: Initial game state

        """

    def on_game_end(self, game_state: GameState, won: bool) -> None:
        """Called when the game ends.

        Args:
            game_state: Final game state
            won: True if this agent won

        """

    def on_turn_start(self, game_state: GameState) -> None:
        """Called at the start of this agent's turn.

        Args:
            game_state: Current game state

        """

    def on_turn_end(self, game_state: GameState) -> None:
        """Called at the end of this agent's turn.

        Args:
            game_state: Current game state

        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(player_id={self.player_id}, name='{self.name}')"
