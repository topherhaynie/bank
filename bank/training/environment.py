"""
Gymnasium Environment Wrapper

Wraps the BANK! game as a Gymnasium environment for RL training.
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False
    gym = None
    spaces = None

from bank.game.engine import BankGame
from bank.game.state import GameState


class BankEnv:
    """
    Gymnasium-compatible environment for BANK! game.
    
    This wrapper allows the game to be used with standard RL frameworks
    like Stable-Baselines3, RLlib, etc.
    
    Note: Requires gymnasium to be installed (included in 'ml' extras)
    """
    
    def __init__(self, num_players: int = 2):
        """
        Initialize the environment.
        
        Args:
            num_players: Number of players in the game
        """
        if not GYMNASIUM_AVAILABLE:
            raise ImportError(
                "Gymnasium is required for training. "
                "Install with: pip install bank-game[ml]"
            )
        
        self.num_players = num_players
        self.game = None
        
        # Define observation and action spaces
        # Observation: [hand_cards (52), bank_cards (52), deck_size, scores (num_players)]
        obs_size = 52 + 52 + 1 + num_players
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(obs_size,), dtype=np.float32
        )
        
        # Action: discrete actions (play_card_0...51, draw_card, bank_card_0...51)
        # This is simplified; actual implementation may vary
        self.action_space = spaces.Discrete(52 + 1 + 52)
        
        self.reset()
    
    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment to initial state.
        
        Args:
            seed: Random seed
            
        Returns:
            Tuple of (observation, info_dict)
        """
        if seed is not None:
            np.random.seed(seed)
        
        player_names = [f"Player {i}" for i in range(self.num_players)]
        self.game = BankGame(num_players=self.num_players, player_names=player_names)
        
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action to take
            
        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        # Decode action
        action_name, params = self._decode_action(action)
        
        # Execute action
        success = self.game.take_action(action_name, **params)
        
        # Calculate reward
        reward = self._calculate_reward(success)
        
        # Check if game is over
        terminated = self.game.is_game_over()
        truncated = False
        
        # Get new observation
        observation = self._get_observation()
        info = self._get_info()
        
        return observation, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """
        Get current observation as numpy array.
        
        Returns:
            Observation vector
        """
        state = self.game.state
        current_player = state.current_player
        
        # One-hot encode hand
        hand_vec = np.zeros(52, dtype=np.float32)
        for card in current_player.hand:
            if 0 <= card - 1 < 52:
                hand_vec[card - 1] = 1.0
        
        # One-hot encode bank
        bank_vec = np.zeros(52, dtype=np.float32)
        for card in current_player.bank:
            if 0 <= card - 1 < 52:
                bank_vec[card - 1] = 1.0
        
        # Deck size (normalized)
        deck_size = np.array([len(state.deck) / 52.0], dtype=np.float32)
        
        # Player scores (normalized)
        scores = np.array(
            [p.score / 100.0 for p in state.players],
            dtype=np.float32
        )
        
        observation = np.concatenate([hand_vec, bank_vec, deck_size, scores])
        return observation
    
    def _get_info(self) -> Dict[str, Any]:
        """Get additional information."""
        return {
            "game_state": self.game.state.to_dict(),
        }
    
    def _decode_action(self, action: int) -> Tuple[str, Dict[str, Any]]:
        """
        Decode integer action to game action.
        
        Args:
            action: Integer action
            
        Returns:
            Tuple of (action_name, parameters)
        """
        # Simplified action decoding
        # 0-51: play_card with card_idx
        # 52: draw_card
        # 53-104: bank_card with card_idx
        
        if action < 52:
            return ("play_card", {"card_idx": action})
        elif action == 52:
            return ("draw_card", {})
        else:
            return ("bank_card", {"card_idx": action - 53})
    
    def _calculate_reward(self, success: bool) -> float:
        """
        Calculate reward for the action.
        
        Args:
            success: Whether action was successful
            
        Returns:
            Reward value
        """
        if not success:
            return -1.0
        
        # Reward based on score change
        state = self.game.state
        current_player = state.current_player
        reward = current_player.score / 10.0
        
        # Bonus for winning
        if state.game_over and state.winner == current_player.player_id:
            reward += 100.0
        
        return reward
    
    def render(self) -> None:
        """Render the current game state (for debugging)."""
        print(self.game.state)
