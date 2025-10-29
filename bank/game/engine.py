"""
BANK! Game Engine

Core game logic and rules implementation.
"""

import random
from typing import List, Optional, Tuple
from bank.game.state import GameState, PlayerState


class BankGame:
    """
    Main game engine for BANK!
    
    This class handles the core game logic, rules, and state management.
    It can be used by both manual agents and AI training frameworks.
    """
    
    def __init__(self, num_players: int = 2, player_names: Optional[List[str]] = None):
        """
        Initialize a new BANK! game.
        
        Args:
            num_players: Number of players (2-6 recommended)
            player_names: Optional list of player names
        """
        if num_players < 2:
            raise ValueError("Must have at least 2 players")
        
        if player_names is None:
            player_names = [f"Player {i+1}" for i in range(num_players)]
        elif len(player_names) != num_players:
            raise ValueError("Number of names must match number of players")
        
        self.state = self._initialize_game(num_players, player_names)
    
    def _initialize_game(self, num_players: int, player_names: List[str]) -> GameState:
        """Initialize a new game state."""
        # Create players
        players = [
            PlayerState(player_id=i, name=name)
            for i, name in enumerate(player_names)
        ]
        
        # Create and shuffle deck (for basic implementation, using numbers 1-52)
        deck = list(range(1, 53))
        random.shuffle(deck)
        
        # Deal initial hands (e.g., 5 cards per player)
        initial_hand_size = 5
        for player in players:
            player.hand = [deck.pop() for _ in range(initial_hand_size)]
        
        return GameState(
            players=players,
            deck=deck,
            discard_pile=[],
            current_player_idx=0,
            round_number=1,
            game_over=False,
            winner=None,
        )
    
    def get_valid_actions(self, player_idx: Optional[int] = None) -> List[str]:
        """
        Get list of valid actions for the current or specified player.
        
        Args:
            player_idx: Player index (defaults to current player)
            
        Returns:
            List of valid action names
        """
        if player_idx is None:
            player_idx = self.state.current_player_idx
        
        if self.state.game_over:
            return []
        
        # Basic action set - extend based on actual game rules
        actions = ["play_card", "draw_card", "bank_card"]
        
        player = self.state.players[player_idx]
        if len(player.hand) == 0:
            actions.remove("play_card")
            actions.remove("bank_card")
        
        if len(self.state.deck) == 0:
            actions.remove("draw_card")
        
        return actions
    
    def take_action(self, action: str, **kwargs) -> bool:
        """
        Execute an action for the current player.
        
        Args:
            action: Action name
            **kwargs: Additional action parameters (e.g., card_idx)
            
        Returns:
            True if action was successful, False otherwise
        """
        if self.state.game_over:
            return False
        
        if action not in self.get_valid_actions():
            return False
        
        # Implement basic actions - extend based on actual game rules
        if action == "play_card":
            return self._play_card(kwargs.get("card_idx", 0))
        elif action == "draw_card":
            return self._draw_card()
        elif action == "bank_card":
            return self._bank_card(kwargs.get("card_idx", 0))
        
        return False
    
    def _play_card(self, card_idx: int) -> bool:
        """Play a card from hand to discard pile."""
        player = self.state.current_player
        if card_idx >= len(player.hand):
            return False
        
        card = player.hand.pop(card_idx)
        self.state.discard_pile.append(card)
        self._next_turn()
        return True
    
    def _draw_card(self) -> bool:
        """Draw a card from the deck."""
        if len(self.state.deck) == 0:
            return False
        
        player = self.state.current_player
        card = self.state.deck.pop()
        player.hand.append(card)
        self._next_turn()
        return True
    
    def _bank_card(self, card_idx: int) -> bool:
        """Bank a card from hand."""
        player = self.state.current_player
        if card_idx >= len(player.hand):
            return False
        
        card = player.hand.pop(card_idx)
        player.bank.append(card)
        player.score += card  # Simple scoring
        self._next_turn()
        return True
    
    def _next_turn(self) -> None:
        """Advance to the next player's turn."""
        self.state.current_player_idx = (
            (self.state.current_player_idx + 1) % self.state.num_players
        )
        
        # Check if round is complete
        if self.state.current_player_idx == 0:
            self.state.round_number += 1
        
        # Check win condition (placeholder - extend based on actual rules)
        self._check_game_over()
    
    def _check_game_over(self) -> None:
        """Check if the game is over and determine winner."""
        # Simple win condition: deck is empty and all players have no cards
        if len(self.state.deck) == 0:
            all_hands_empty = all(len(p.hand) == 0 for p in self.state.players)
            if all_hands_empty:
                self.state.game_over = True
                # Winner is player with highest score
                winner_idx = max(
                    range(len(self.state.players)),
                    key=lambda i: self.state.players[i].score
                )
                self.state.winner = winner_idx
    
    def reset(self) -> GameState:
        """Reset the game to initial state."""
        player_names = [p.name for p in self.state.players]
        num_players = len(player_names)
        self.state = self._initialize_game(num_players, player_names)
        return self.state
    
    def get_state(self) -> GameState:
        """Get the current game state."""
        return self.state
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.state.game_over
    
    def get_winner(self) -> Optional[PlayerState]:
        """Get the winning player if game is over."""
        if self.state.winner is not None:
            return self.state.players[self.state.winner]
        return None
