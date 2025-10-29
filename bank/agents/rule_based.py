"""
Rule-Based Agent

A simple rule-based agent that follows predefined strategies.
This serves as a template for creating manual/programmed agents.
"""

from typing import Dict, Any, Tuple
from bank.game.state import GameState
from bank.agents.base import BaseAgent


class RuleBasedAgent(BaseAgent):
    """
    Agent that follows simple rules to make decisions.
    
    This is a template for creating more sophisticated rule-based agents.
    Users can extend this class or create similar agents with custom strategies.
    """
    
    def __init__(self, player_id: int, name: str = "RuleBot"):
        """
        Initialize the rule-based agent.
        
        Args:
            player_id: The player ID this agent controls
            name: The agent's name
        """
        super().__init__(player_id, name)
    
    def select_action(self, game_state: GameState, valid_actions: list) -> Tuple[str, Dict[str, Any]]:
        """
        Select action based on simple rules.
        
        Strategy:
        1. If we can bank a high-value card, do it
        2. Otherwise, draw a card if possible
        3. If hand is full, play lowest card
        
        Args:
            game_state: Current game state
            valid_actions: List of valid action names
            
        Returns:
            Tuple of (action_name, action_parameters)
        """
        if not valid_actions:
            return ("pass", {})
        
        player = game_state.players[self.player_id]
        
        # Strategy: Bank high-value cards (> 40)
        if "bank_card" in valid_actions and player.hand:
            high_value_cards = [
                (idx, card) for idx, card in enumerate(player.hand) if card > 40
            ]
            if high_value_cards:
                best_idx, _ = max(high_value_cards, key=lambda x: x[1])
                return ("bank_card", {"card_idx": best_idx})
        
        # Strategy: Draw cards when hand is small
        if "draw_card" in valid_actions and len(player.hand) < 5:
            return ("draw_card", {})
        
        # Strategy: Play lowest value card
        if "play_card" in valid_actions and player.hand:
            lowest_idx = min(range(len(player.hand)), key=lambda i: player.hand[i])
            return ("play_card", {"card_idx": lowest_idx})
        
        # Fallback to first valid action
        return (valid_actions[0], {})
