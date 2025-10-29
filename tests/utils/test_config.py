"""
Tests for configuration utilities.
"""

import pytest
import json
import tempfile
from pathlib import Path
from bank.utils.config import Config


def test_default_config():
    """Test that default configuration loads correctly."""
    config = Config()
    
    assert config.get("game.num_players") == 2
    assert config.get("training.episodes") == 1000


def test_get_config_value():
    """Test getting configuration values."""
    config = Config()
    
    # Test existing keys
    assert config.get("game.num_players") == 2
    assert config.get("training.learning_rate") == 0.001
    
    # Test non-existing key with default
    assert config.get("nonexistent.key", default="default") == "default"


def test_set_config_value():
    """Test setting configuration values."""
    config = Config()
    
    config.set("game.num_players", 4)
    assert config.get("game.num_players") == 4
    
    config.set("new_key.nested", "value")
    assert config.get("new_key.nested") == "value"


def test_save_and_load_config():
    """Test saving and loading configuration."""
    config1 = Config()
    config1.set("game.num_players", 4)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # Save config
        config1.save(temp_path)
        
        # Load config
        config2 = Config(temp_path)
        assert config2.get("game.num_players") == 4
        
    finally:
        Path(temp_path).unlink()


def test_merge_config():
    """Test merging custom configuration."""
    config = Config()
    
    custom_config = {
        "game": {
            "num_players": 6
        },
        "new_section": {
            "key": "value"
        }
    }
    
    config._merge_config(custom_config)
    
    assert config.get("game.num_players") == 6
    assert config.get("new_section.key") == "value"
    # Check that other game settings are preserved
    assert config.get("game.initial_hand_size") == 5
