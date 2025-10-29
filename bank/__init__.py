"""
BANK! Game Package

A modular game environment for the BANK! card game with support for:
- Manual agents (human and programmed)
- Deep Q-Network (DQN) reinforcement learning agents
- Command-line interface for gameplay
"""

__version__ = "0.1.0"
__author__ = "topherhaynie"

from bank.game.engine import BankGame
from bank.game.state import GameState

__all__ = ["BankGame", "GameState", "__version__"]
