"""
Game State

Represents the current state of the BANK! game.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class PlayerState:
    """Represents the state of a single player."""
    
    player_id: int
    name: str
    hand: List[int] = field(default_factory=list)
    bank: List[int] = field(default_factory=list)
    score: int = 0
    
    def __repr__(self) -> str:
        return f"Player({self.name}, score={self.score}, hand={len(self.hand)}, bank={len(self.bank)})"


@dataclass
class GameState:
    """Represents the complete state of the BANK! game."""
    
    players: List[PlayerState]
    deck: List[int]
    discard_pile: List[int] = field(default_factory=list)
    current_player_idx: int = 0
    round_number: int = 1
    game_over: bool = False
    winner: Optional[int] = None
    
    @property
    def current_player(self) -> PlayerState:
        """Get the current player."""
        return self.players[self.current_player_idx]
    
    @property
    def num_players(self) -> int:
        """Get the number of players."""
        return len(self.players)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the game state to a dictionary."""
        return {
            "players": [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "hand_size": len(p.hand),
                    "bank_size": len(p.bank),
                    "score": p.score,
                }
                for p in self.players
            ],
            "deck_size": len(self.deck),
            "discard_pile_size": len(self.discard_pile),
            "current_player_idx": self.current_player_idx,
            "round_number": self.round_number,
            "game_over": self.game_over,
            "winner": self.winner,
        }
    
    def __repr__(self) -> str:
        return (
            f"GameState(round={self.round_number}, "
            f"current_player={self.current_player.name}, "
            f"players={self.num_players}, game_over={self.game_over})"
        )
