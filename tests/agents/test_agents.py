"""
Tests for agent implementations.
"""

import pytest
from bank.game.engine import BankGame
from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import RuleBasedAgent


def test_random_agent_creation():
    """Test creating a random agent."""
    agent = RandomAgent(player_id=0, name="TestBot")
    
    assert agent.player_id == 0
    assert agent.name == "TestBot"


def test_random_agent_select_action():
    """Test random agent action selection."""
    game = BankGame(num_players=2)
    agent = RandomAgent(player_id=0, seed=42)
    
    valid_actions = game.get_valid_actions()
    action, params = agent.select_action(game.state, valid_actions)
    
    assert action in valid_actions
    assert isinstance(params, dict)


def test_random_agent_with_seed():
    """Test that random agent with seed is reproducible."""
    game1 = BankGame(num_players=2)
    game2 = BankGame(num_players=2)
    
    agent1 = RandomAgent(player_id=0, seed=42)
    agent2 = RandomAgent(player_id=0, seed=42)
    
    valid_actions = game1.get_valid_actions()
    action1, params1 = agent1.select_action(game1.state, valid_actions)
    action2, params2 = agent2.select_action(game2.state, valid_actions)
    
    assert action1 == action2


def test_rule_based_agent_creation():
    """Test creating a rule-based agent."""
    agent = RuleBasedAgent(player_id=0, name="RuleBot")
    
    assert agent.player_id == 0
    assert agent.name == "RuleBot"


def test_rule_based_agent_select_action():
    """Test rule-based agent action selection."""
    game = BankGame(num_players=2)
    agent = RuleBasedAgent(player_id=0)
    
    valid_actions = game.get_valid_actions()
    action, params = agent.select_action(game.state, valid_actions)
    
    assert action in valid_actions
    assert isinstance(params, dict)


def test_agent_callbacks():
    """Test agent lifecycle callbacks."""
    game = BankGame(num_players=2)
    agent = RandomAgent(player_id=0)
    
    # These should not raise errors
    agent.on_game_start(game.state)
    agent.on_turn_start(game.state)
    agent.on_turn_end(game.state)
    agent.on_game_end(game.state, won=True)


def test_agent_repr():
    """Test agent string representation."""
    agent = RandomAgent(player_id=0, name="TestBot")
    repr_str = repr(agent)
    
    assert "RandomAgent" in repr_str
    assert "0" in repr_str
    assert "TestBot" in repr_str
