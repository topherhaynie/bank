"""
Random Agent

A simple agent that selects actions randomly. Useful for testing and as a baseline.
"""

import random
from typing import Dict, Any, Tuple
from bank.game.state import GameState
from bank.agents.base import BaseAgent


class RandomAgent(BaseAgent):
    """
    Agent that randomly selects from valid actions.
    
    Useful as a baseline and for testing game mechanics.
    """
    
    def __init__(self, player_id: int, name: str = "RandomBot", seed: int = None):
        """
        Initialize the random agent.
        
        Args:
            player_id: The player ID this agent controls
            name: The agent's name
            seed: Random seed for reproducibility (optional)
        """
        super().__init__(player_id, name)
        self.rng = random.Random(seed)
    
    def select_action(self, game_state: GameState, valid_actions: list) -> Tuple[str, Dict[str, Any]]:
        """
        Randomly select an action from valid actions.
        
        Args:
            game_state: Current game state
            valid_actions: List of valid action names
            
        Returns:
            Tuple of (action_name, action_parameters)
        """
        if not valid_actions:
            return ("pass", {})
        
        action = self.rng.choice(valid_actions)
        params = {}
        
        # Add random parameters for actions that need them
        player = game_state.players[self.player_id]
        
        if action in ["play_card", "bank_card"] and player.hand:
            params["card_idx"] = self.rng.randint(0, len(player.hand) - 1)
        
        return (action, params)
