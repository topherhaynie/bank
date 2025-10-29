"""
Base Agent Interface

Defines the interface that all agents (manual, AI, etc.) must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from bank.game.state import GameState


class BaseAgent(ABC):
    """
    Abstract base class for all BANK! game agents.
    
    All agents (human, random, rule-based, DQN, etc.) should inherit from this class.
    """
    
    def __init__(self, player_id: int, name: str):
        """
        Initialize the agent.
        
        Args:
            player_id: The player ID this agent controls
            name: The agent's name
        """
        self.player_id = player_id
        self.name = name
    
    @abstractmethod
    def select_action(self, game_state: GameState, valid_actions: list) -> Tuple[str, Dict[str, Any]]:
        """
        Select an action to take given the current game state.
        
        Args:
            game_state: Current game state
            valid_actions: List of valid action names
            
        Returns:
            Tuple of (action_name, action_parameters)
        """
        pass
    
    def on_game_start(self, game_state: GameState) -> None:
        """
        Called when a new game starts.
        
        Args:
            game_state: Initial game state
        """
        pass
    
    def on_game_end(self, game_state: GameState, won: bool) -> None:
        """
        Called when the game ends.
        
        Args:
            game_state: Final game state
            won: True if this agent won
        """
        pass
    
    def on_turn_start(self, game_state: GameState) -> None:
        """
        Called at the start of this agent's turn.
        
        Args:
            game_state: Current game state
        """
        pass
    
    def on_turn_end(self, game_state: GameState) -> None:
        """
        Called at the end of this agent's turn.
        
        Args:
            game_state: Current game state
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(player_id={self.player_id}, name='{self.name}')"
