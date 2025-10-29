"""Game state representations for the BANK! dice game."""

from dataclasses import dataclass, field
from typing import Any

# Magic number for first three rolls special rules
FIRST_THREE_ROLLS = 3


@dataclass
class PlayerState:
    """Represents the state of a single player in the BANK! dice game.

    Attributes:
        player_id: Unique identifier for the player
        name: Display name for the player
        score: Total accumulated score across all rounds
        has_banked_this_round: Whether the player has banked in the current round

    """

    player_id: int
    name: str
    score: int = 0
    has_banked_this_round: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert player state to a dictionary for serialization."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "score": self.score,
            "has_banked_this_round": self.has_banked_this_round,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlayerState":
        """Create a PlayerState from a dictionary."""
        return cls(
            player_id=data["player_id"],
            name=data["name"],
            score=data["score"],
            has_banked_this_round=data["has_banked_this_round"],
        )

    def __repr__(self) -> str:
        """Return a string representation of the player state."""
        return f"Player({self.name}, score={self.score}, banked={self.has_banked_this_round})"


@dataclass
class RoundState:
    """Represents the state of the current round in the BANK! game.

    Attributes:
        round_number: Current round number (1-based)
        roll_count: Number of rolls made in this round (1-based)
        current_bank: Current points available in the bank
        last_roll: The most recent dice roll (die1, die2) or None if no roll yet
        active_player_ids: Set of player IDs still active (not yet banked) in this round

    """

    round_number: int
    roll_count: int = 0
    current_bank: int = 0
    last_roll: tuple[int, int] | None = None
    active_player_ids: set[int] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        """Convert round state to a dictionary for serialization."""
        return {
            "round_number": self.round_number,
            "roll_count": self.roll_count,
            "current_bank": self.current_bank,
            "last_roll": list(self.last_roll) if self.last_roll else None,
            "active_player_ids": list(self.active_player_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoundState":
        """Create a RoundState from a dictionary."""
        last_roll = tuple(data["last_roll"]) if data["last_roll"] else None
        return cls(
            round_number=data["round_number"],
            roll_count=data["roll_count"],
            current_bank=data["current_bank"],
            last_roll=last_roll,
            active_player_ids=set(data["active_player_ids"]),
        )

    def is_first_three_rolls(self) -> bool:
        """Check if we're in the first three rolls of the round (special rules apply)."""
        return 1 <= self.roll_count <= FIRST_THREE_ROLLS

    def __repr__(self) -> str:
        """Return a string representation of the round state."""
        return (
            f"Round({self.round_number}, roll={self.roll_count}, "
            f"bank={self.current_bank}, active={len(self.active_player_ids)})"
        )


@dataclass
class GameState:
    """Represents the complete state of the BANK! dice game.

    Attributes:
        players: List of all players in the game
        current_round: Current round state, or None if game hasn't started
        total_rounds: Total number of rounds to play (10, 15, or 20)
        game_over: Whether the game has ended
        winner: Player ID of the winner, or None if game isn't over

    """

    players: list[PlayerState]
    total_rounds: int = 10
    current_round: RoundState | None = None
    game_over: bool = False
    winner: int | None = None

    @property
    def num_players(self) -> int:
        """Get the number of players in the game."""
        return len(self.players)

    def get_player(self, player_id: int) -> PlayerState | None:
        """Get a player by their ID."""
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None

    def get_active_players(self) -> list[PlayerState]:
        """Get list of players still active (not banked) in the current round."""
        if not self.current_round:
            return []
        return [player for player in self.players if player.player_id in self.current_round.active_player_ids]

    def get_leading_player(self) -> PlayerState | None:
        """Get the player with the highest score."""
        if not self.players:
            return None
        return max(self.players, key=lambda p: p.score)

    def to_dict(self) -> dict[str, Any]:
        """Convert the game state to a dictionary for serialization."""
        return {
            "players": [p.to_dict() for p in self.players],
            "total_rounds": self.total_rounds,
            "current_round": self.current_round.to_dict() if self.current_round else None,
            "game_over": self.game_over,
            "winner": self.winner,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        """Create a GameState from a dictionary."""
        players = [PlayerState.from_dict(p) for p in data["players"]]
        current_round = RoundState.from_dict(data["current_round"]) if data["current_round"] else None
        return cls(
            players=players,
            total_rounds=data["total_rounds"],
            current_round=current_round,
            game_over=data["game_over"],
            winner=data["winner"],
        )

    def __repr__(self) -> str:
        """Return a string representation of the game state."""
        if self.current_round:
            round_info = f"round={self.current_round.round_number}/{self.total_rounds}"
        else:
            round_info = "not started"
        return f"GameState({round_info}, players={self.num_players}, game_over={self.game_over})"
