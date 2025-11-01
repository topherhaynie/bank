"""Agents module.

Contains agent implementations for playing BANK!
- Base agent interface
- Manual/programmed agents
- Random agent for testing
- Rule-based agents (threshold, conservative, aggressive, smart, adaptive)
- Advanced strategic agents (leader-based, leech, rank-based)
"""

from bank.agents.advanced_agents import (
    LeaderOnlyAgent,
    LeaderPlusOneAgent,
    LeechAgent,
    RankBasedAgent,
)
from bank.agents.base import Action, Agent, Observation
from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import (
    AdaptiveAgent,
    AggressiveAgent,
    ConservativeAgent,
    SmartAgent,
    ThresholdAgent,
)

__all__ = [
    "Action",
    "AdaptiveAgent",
    "Agent",
    "AggressiveAgent",
    "ConservativeAgent",
    "LeaderOnlyAgent",
    "LeaderPlusOneAgent",
    "LeechAgent",
    "Observation",
    "RandomAgent",
    "RankBasedAgent",
    "SmartAgent",
    "ThresholdAgent",
]
