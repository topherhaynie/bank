"""
DQN Agent Implementation

Deep Q-Network agent for playing BANK!
"""

from typing import Optional, Tuple, Dict, Any
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None
    optim = None

from bank.agents.base import BaseAgent
from bank.game.state import GameState


class DQNetwork(nn.Module if TORCH_AVAILABLE else object):
    """
    Deep Q-Network architecture.
    
    A simple feedforward network for Q-value estimation.
    """
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: list = None):
        """
        Initialize the network.
        
        Args:
            state_dim: Dimension of state space
            action_dim: Number of possible actions
            hidden_dims: List of hidden layer dimensions
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for DQN. Install with: pip install bank-game[ml]")
        
        super().__init__()
        
        if hidden_dims is None:
            hidden_dims = [128, 128]
        
        layers = []
        prev_dim = state_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, action_dim))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        """Forward pass through the network."""
        return self.network(x)


class DQNAgent(BaseAgent):
    """
    Deep Q-Network agent for BANK!
    
    This agent uses deep reinforcement learning to learn optimal strategies.
    """
    
    def __init__(
        self,
        player_id: int,
        name: str = "DQN-Agent",
        state_dim: int = 107,  # Matches BankEnv observation space
        action_dim: int = 105,  # Matches BankEnv action space
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
    ):
        """
        Initialize the DQN agent.
        
        Args:
            player_id: Player ID
            name: Agent name
            state_dim: State space dimension
            action_dim: Action space dimension
            learning_rate: Learning rate
            gamma: Discount factor
            epsilon: Initial exploration rate
            epsilon_min: Minimum exploration rate
            epsilon_decay: Exploration decay rate
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for DQN. Install with: pip install bank-game[ml]")
        
        super().__init__(player_id, name)
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        
        # Initialize networks
        self.q_network = DQNetwork(state_dim, action_dim)
        self.target_network = DQNetwork(state_dim, action_dim)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        self.loss_fn = nn.MSELoss()
        
        # Experience replay buffer
        self.memory = []
        self.memory_size = 10000
    
    def select_action(self, game_state: GameState, valid_actions: list) -> Tuple[str, Dict[str, Any]]:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            game_state: Current game state
            valid_actions: List of valid actions
            
        Returns:
            Tuple of (action_name, action_parameters)
        """
        # Convert game state to observation
        state_vector = self._state_to_vector(game_state)
        
        # Epsilon-greedy action selection
        if np.random.random() < self.epsilon:
            # Explore: random action
            action_idx = np.random.randint(0, self.action_dim)
        else:
            # Exploit: best action from Q-network
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state_vector).unsqueeze(0)
                q_values = self.q_network(state_tensor)
                action_idx = q_values.argmax().item()
        
        # Decode action
        return self._decode_action(action_idx, game_state)
    
    def _state_to_vector(self, game_state: GameState) -> np.ndarray:
        """Convert game state to feature vector."""
        # Simplified state representation
        # In practice, this should match the BankEnv observation space
        current_player = game_state.players[self.player_id]
        
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
        deck_size = np.array([len(game_state.deck) / 52.0], dtype=np.float32)
        
        # Player scores (normalized)
        scores = np.array(
            [p.score / 100.0 for p in game_state.players],
            dtype=np.float32
        )
        
        return np.concatenate([hand_vec, bank_vec, deck_size, scores])
    
    def _decode_action(self, action_idx: int, game_state: GameState) -> Tuple[str, Dict[str, Any]]:
        """Decode action index to game action."""
        # Simplified action decoding
        if action_idx < 52:
            return ("play_card", {"card_idx": min(action_idx, len(game_state.current_player.hand) - 1)})
        elif action_idx == 52:
            return ("draw_card", {})
        else:
            return ("bank_card", {"card_idx": min(action_idx - 53, len(game_state.current_player.hand) - 1)})
    
    def update_epsilon(self) -> None:
        """Decay exploration rate."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def save_model(self, path: str) -> None:
        """Save model weights."""
        torch.save(self.q_network.state_dict(), path)
    
    def load_model(self, path: str) -> None:
        """Load model weights."""
        self.q_network.load_state_dict(torch.load(path))
        self.target_network.load_state_dict(self.q_network.state_dict())
