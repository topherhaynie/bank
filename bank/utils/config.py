"""
Configuration utilities for BANK!
"""

import json
from typing import Dict, Any
from pathlib import Path


class Config:
    """Configuration manager for BANK! game and training."""
    
    DEFAULT_CONFIG = {
        "game": {
            "num_players": 2,
            "initial_hand_size": 5,
            "deck_size": 52,
        },
        "training": {
            "episodes": 1000,
            "learning_rate": 0.001,
            "gamma": 0.99,
            "epsilon_start": 1.0,
            "epsilon_min": 0.01,
            "epsilon_decay": 0.995,
            "batch_size": 32,
            "memory_size": 10000,
        },
        "cli": {
            "ai_delay": 0.5,
        }
    }
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to JSON config file (optional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_path and Path(config_path).exists():
            self.load(config_path)
    
    def load(self, path: str) -> None:
        """Load configuration from JSON file."""
        with open(path, 'r') as f:
            custom_config = json.load(f)
            self._merge_config(custom_config)
    
    def save(self, path: str) -> None:
        """Save configuration to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _merge_config(self, custom_config: Dict[str, Any]) -> None:
        """Merge custom config with defaults."""
        for key, value in custom_config.items():
            if key in self.config and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
