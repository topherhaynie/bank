"""Integration tests for BANK! dice game agents.

Tests all baseline agents (Random, Threshold, Conservative, Aggressive, Smart, Adaptive)
to ensure they:
- Work correctly with the game engine
- Respect the can_bank constraint
- Handle edge cases properly
- Produce deterministic results when seeded
- Complete full games without errors
"""

from __future__ import annotations

import random

from bank.agents.base import Observation
from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import (
    AdaptiveAgent,
    AggressiveAgent,
    ConservativeAgent,
    SmartAgent,
    ThresholdAgent,
)
from bank.game.engine import BankGame


class TestAgentBasics:
    """Test basic agent creation and interface compliance."""

    def test_random_agent_creation(self) -> None:
        """Test creating a RandomAgent."""
        agent = RandomAgent(player_id=0, name="TestBot", seed=42)

        assert agent.player_id == 0
        assert agent.name == "TestBot"
        assert agent.rng is not None

    def test_random_agent_default_name(self) -> None:
        """Test RandomAgent with default name."""
        agent = RandomAgent(player_id=3)

        assert agent.player_id == 3
        assert agent.name == "RandomBot-3"

    def test_threshold_agent_creation(self) -> None:
        """Test creating a ThresholdAgent."""
        agent = ThresholdAgent(player_id=1, threshold=75, name="T75")

        assert agent.player_id == 1
        assert agent.threshold == 75
        assert agent.name == "T75"

    def test_threshold_agent_default_name(self) -> None:
        """Test ThresholdAgent with default name."""
        agent = ThresholdAgent(player_id=0, threshold=60)

        assert agent.name == "Threshold-60"

    def test_conservative_agent_creation(self) -> None:
        """Test creating a ConservativeAgent."""
        agent = ConservativeAgent(player_id=2, early_threshold=25, late_threshold=15)

        assert agent.player_id == 2
        assert agent.early_threshold == 25
        assert agent.late_threshold == 15

    def test_aggressive_agent_creation(self) -> None:
        """Test creating an AggressiveAgent."""
        agent = AggressiveAgent(player_id=0, min_threshold=100)

        assert agent.player_id == 0
        assert agent.min_threshold == 100

    def test_smart_agent_creation(self) -> None:
        """Test creating a SmartAgent."""
        agent = SmartAgent(player_id=1, base_threshold=55)

        assert agent.player_id == 1
        assert agent.base_threshold == 55

    def test_adaptive_agent_creation(self) -> None:
        """Test creating an AdaptiveAgent."""
        agent = AdaptiveAgent(player_id=3, default_threshold=45)

        assert agent.player_id == 3
        assert agent.default_threshold == 45


class TestAgentActions:
    """Test agent decision-making with mock observations."""

    def test_random_agent_respects_can_bank(self) -> None:
        """RandomAgent should only pass when can_bank is False."""
        agent = RandomAgent(player_id=0, seed=42)

        observation: Observation = {
            "round_number": 1,
            "roll_count": 4,
            "current_bank": 50,
            "last_roll": (3, 4),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 20,
            "can_bank": False,
            "all_player_scores": {0: 20, 1: 25},
        }

        action = agent.act(observation)
        assert action == "pass"

    def test_threshold_agent_banks_at_threshold(self) -> None:
        """ThresholdAgent should bank when threshold is met."""
        agent = ThresholdAgent(player_id=0, threshold=50)

        observation: Observation = {
            "round_number": 1,
            "roll_count": 4,
            "current_bank": 50,
            "last_roll": (3, 4),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 20,
            "can_bank": True,
            "all_player_scores": {0: 20, 1: 25},
        }

        action = agent.act(observation)
        assert action == "bank"

    def test_threshold_agent_passes_below_threshold(self) -> None:
        """ThresholdAgent should pass when below threshold."""
        agent = ThresholdAgent(player_id=0, threshold=50)

        observation: Observation = {
            "round_number": 1,
            "roll_count": 3,
            "current_bank": 49,
            "last_roll": (2, 5),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 20,
            "can_bank": True,
            "all_player_scores": {0: 20, 1: 25},
        }

        action = agent.act(observation)
        assert action == "pass"

    def test_conservative_agent_banks_early_after_roll_3(self) -> None:
        """ConservativeAgent should use lower threshold after roll 3."""
        agent = ConservativeAgent(player_id=0, early_threshold=50, late_threshold=25)

        # After roll 3, should use late_threshold (25)
        observation: Observation = {
            "round_number": 1,
            "roll_count": 4,
            "current_bank": 30,
            "last_roll": (2, 4),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 10,
            "can_bank": True,
            "all_player_scores": {0: 10, 1: 15},
        }

        action = agent.act(observation)
        assert action == "bank"  # 30 >= late_threshold (25)

    def test_conservative_agent_waits_during_first_3_rolls(self) -> None:
        """ConservativeAgent should use higher threshold during first 3 rolls."""
        agent = ConservativeAgent(player_id=0, early_threshold=50, late_threshold=25)

        # During first 3 rolls, should use early_threshold (50)
        observation: Observation = {
            "round_number": 1,
            "roll_count": 2,
            "current_bank": 30,
            "last_roll": (1, 6),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 10,
            "can_bank": True,
            "all_player_scores": {0: 10, 1: 15},
        }

        action = agent.act(observation)
        assert action == "pass"  # 30 < early_threshold (50)

    def test_aggressive_agent_waits_for_high_values(self) -> None:
        """AggressiveAgent should pass on moderate values."""
        agent = AggressiveAgent(player_id=0, min_threshold=80)

        observation: Observation = {
            "round_number": 1,
            "roll_count": 5,
            "current_bank": 60,
            "last_roll": (4, 5),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 50,
            "can_bank": True,
            "all_player_scores": {0: 50, 1: 45},
        }

        action = agent.act(observation)
        assert action == "pass"  # 60 < min_threshold (80)

    def test_smart_agent_banks_as_last_player(self) -> None:
        """SmartAgent should bank if last active player with reasonable bank."""
        agent = SmartAgent(player_id=0, base_threshold=50)

        observation: Observation = {
            "round_number": 1,
            "roll_count": 5,
            "current_bank": 25,
            "last_roll": (3, 3),
            "active_player_ids": {0},  # Only player left
            "player_id": 0,
            "player_score": 30,
            "can_bank": True,
            "all_player_scores": {0: 30, 1: 40},
        }

        action = agent.act(observation)
        assert action == "bank"  # Last player, bank >= 20

    def test_smart_agent_passes_on_tiny_amounts(self) -> None:
        """SmartAgent should never bank trivial amounts."""
        agent = SmartAgent(player_id=0, base_threshold=50)

        observation: Observation = {
            "round_number": 1,
            "roll_count": 2,
            "current_bank": 10,
            "last_roll": (1, 4),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 20,
            "can_bank": True,
            "all_player_scores": {0: 20, 1: 25},
        }

        action = agent.act(observation)
        assert action == "pass"  # Bank < 15, always pass

    def test_adaptive_agent_conservative_when_leading(self) -> None:
        """AdaptiveAgent should use lower threshold when significantly ahead."""
        agent = AdaptiveAgent(player_id=0, default_threshold=50)

        observation: Observation = {
            "round_number": 5,
            "roll_count": 4,
            "current_bank": 35,
            "last_roll": (2, 3),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 150,  # Significantly ahead
            "can_bank": True,
            "all_player_scores": {0: 150, 1: 80},  # Leading by 70
        }

        action = agent.act(observation)
        # With score_diff >= 50, threshold is ~30 (50 * 0.6)
        assert action == "bank"  # 35 >= 30

    def test_adaptive_agent_aggressive_when_behind(self) -> None:
        """AdaptiveAgent should use higher threshold when behind."""
        agent = AdaptiveAgent(player_id=0, default_threshold=50)

        observation: Observation = {
            "round_number": 5,
            "roll_count": 4,
            "current_bank": 60,
            "last_roll": (5, 5),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 80,  # Behind
            "can_bank": True,
            "all_player_scores": {0: 80, 1: 150},  # Behind by 70
        }

        action = agent.act(observation)
        # With score_diff <= -50, threshold is ~80 (50 * 1.6)
        # 60 < 80, so should pass
        assert action == "pass"


class TestAgentWithEngine:
    """Test agents integrated with the game engine."""

    def test_random_agent_completes_game(self) -> None:
        """RandomAgent should complete a full game without errors."""
        agents = [RandomAgent(0, seed=42), RandomAgent(1, seed=43)]
        game = BankGame(
            num_players=2,
            agents=agents,
            total_rounds=5,
            rng=random.Random(100),
        )

        game.play_game()

        assert game.state.game_over
        # Game completed all rounds
        assert game.state.current_round is not None
        assert game.state.current_round.round_number == 5
        winner = game.get_winner()
        assert winner is not None

    def test_threshold_agents_complete_game(self) -> None:
        """ThresholdAgents with different thresholds should complete game."""
        agents = [
            ThresholdAgent(0, threshold=40),
            ThresholdAgent(1, threshold=60),
        ]
        game = BankGame(
            num_players=2,
            agents=agents,
            total_rounds=5,
            rng=random.Random(200),
        )

        game.play_game()

        assert game.state.game_over
        winner = game.get_winner()
        assert winner is not None

    def test_mixed_agents_complete_game(self) -> None:
        """Mixed agent types should work together."""
        agents = [
            RandomAgent(0, seed=50),
            ThresholdAgent(1, threshold=50),
            ConservativeAgent(2),
            AggressiveAgent(3),
        ]
        game = BankGame(
            num_players=4,
            agents=agents,
            total_rounds=3,
            rng=random.Random(300),
        )

        game.play_game()

        assert game.state.game_over
        # Game completed all rounds
        assert game.state.current_round is not None
        assert game.state.current_round.round_number == 3

    def test_all_rule_based_agents_together(self) -> None:
        """All rule-based agents should work in same game."""
        agents = [
            ThresholdAgent(0, threshold=50),
            ConservativeAgent(1),
            AggressiveAgent(2),
            SmartAgent(3),
            AdaptiveAgent(4),
        ]
        game = BankGame(
            num_players=5,
            agents=agents,
            total_rounds=5,
            rng=random.Random(400),
        )

        game.play_game()

        assert game.state.game_over
        # Check all players got their scores updated
        for player in game.state.players:
            assert player.score >= 0

    def test_agents_respect_can_bank_in_game(self) -> None:
        """Agents should only bank when allowed in actual game."""
        agents = [ThresholdAgent(0, threshold=20), ThresholdAgent(1, threshold=20)]
        game = BankGame(
            num_players=2,
            agents=agents,
            total_rounds=3,
            rng=random.Random(500),
        )

        # Play one round
        game.start_new_round()

        # First roll
        game.roll_dice()
        decisions = game.poll_decisions()

        # Both should be able to bank initially
        for player_id in decisions:
            player = game.state.get_player(player_id)
            assert player is not None
            # If player banked, they shouldn't be able to bank again
            if player.has_banked_this_round:
                observation = game.create_observation(player_id)
                assert not observation["can_bank"]


class TestAgentDeterminism:
    """Test that agents with seeds produce deterministic results."""

    def test_random_agent_determinism(self) -> None:
        """RandomAgent with same seed should make same decisions."""
        observation: Observation = {
            "round_number": 1,
            "roll_count": 4,
            "current_bank": 50,
            "last_roll": (3, 4),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 20,
            "can_bank": True,
            "all_player_scores": {0: 20, 1: 25},
        }

        agent1 = RandomAgent(0, seed=999)
        agent2 = RandomAgent(0, seed=999)

        actions1 = [agent1.act(observation) for _ in range(10)]
        actions2 = [agent2.act(observation) for _ in range(10)]

        assert actions1 == actions2

    def test_game_with_seeded_agents_deterministic(self) -> None:
        """Full game with seeded agents and RNG should be deterministic."""
        # Game 1
        agents1 = [RandomAgent(0, seed=111), RandomAgent(1, seed=222)]
        game1 = BankGame(
            num_players=2,
            agents=agents1,
            total_rounds=3,
            rng=random.Random(333),
        )
        game1.play_game()
        scores1 = {p.player_id: p.score for p in game1.state.players}

        # Game 2 with same seeds
        agents2 = [RandomAgent(0, seed=111), RandomAgent(1, seed=222)]
        game2 = BankGame(
            num_players=2,
            agents=agents2,
            total_rounds=3,
            rng=random.Random(333),
        )
        game2.play_game()
        scores2 = {p.player_id: p.score for p in game2.state.players}

        # Results should be identical
        assert scores1 == scores2
        assert game1.get_winner() == game2.get_winner()


class TestAgentEdgeCases:
    """Test agent behavior in edge cases and boundary conditions."""

    def test_agent_with_zero_bank(self) -> None:
        """Agents should handle zero bank value correctly."""
        agent = ThresholdAgent(0, threshold=30)

        observation: Observation = {
            "round_number": 1,
            "roll_count": 1,
            "current_bank": 0,
            "last_roll": None,
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 0,
            "can_bank": True,
            "all_player_scores": {0: 0, 1: 0},
        }

        action = agent.act(observation)
        assert action == "pass"  # 0 < 30

    def test_agent_with_no_last_roll(self) -> None:
        """Agents should handle None last_roll (start of round)."""
        agent = SmartAgent(0)

        observation: Observation = {
            "round_number": 1,
            "roll_count": 1,
            "current_bank": 0,
            "last_roll": None,  # No roll yet
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 0,
            "can_bank": True,
            "all_player_scores": {0: 0, 1: 0},
        }

        # Should not crash
        action = agent.act(observation)
        assert action in ["bank", "pass"]

    def test_agent_as_only_active_player(self) -> None:
        """Agents should handle being the only active player."""
        agent = SmartAgent(0, base_threshold=50)

        observation: Observation = {
            "round_number": 2,
            "roll_count": 6,
            "current_bank": 25,
            "last_roll": (4, 4),
            "active_player_ids": {0},  # Only one left
            "player_id": 0,
            "player_score": 100,
            "can_bank": True,
            "all_player_scores": {0: 100, 1: 90, 2: 85},
        }

        action = agent.act(observation)
        assert action == "bank"  # Should bank when alone

    def test_agent_in_two_player_game(self) -> None:
        """Agent should work in minimal two-player game."""
        agents = [ThresholdAgent(0, threshold=40), ThresholdAgent(1, threshold=40)]
        game = BankGame(
            num_players=2,
            agents=agents,
            total_rounds=3,
            rng=random.Random(600),
        )

        game.play_game()

        assert game.state.game_over
        assert len(game.state.players) == 2
        # At least one player should have scored
        total_score = sum(p.score for p in game.state.players)
        assert total_score > 0

    def test_agent_with_very_high_threshold(self) -> None:
        """Agent with unreachable threshold should still complete game."""
        agents = [ThresholdAgent(0, threshold=10000), ThresholdAgent(1, threshold=50)]
        game = BankGame(
            num_players=2,
            agents=agents,
            total_rounds=3,
            rng=random.Random(700),
        )

        game.play_game()

        assert game.state.game_over
        # Agent with high threshold might never bank, could have score 0
        player0 = game.state.get_player(0)
        player1 = game.state.get_player(1)
        assert player0 is not None
        assert player1 is not None
        # At least one player should have scored
        assert player0.score + player1.score > 0


class TestAgentReset:
    """Test agent reset functionality."""

    def test_random_agent_reset(self) -> None:
        """RandomAgent reset should not crash."""
        agent = RandomAgent(0, seed=42)
        agent.reset()
        # Should not raise any errors

    def test_threshold_agent_reset(self) -> None:
        """ThresholdAgent reset should not crash."""
        agent = ThresholdAgent(0, threshold=50)
        agent.reset()
        # Should not raise any errors

    def test_all_agents_reset(self) -> None:
        """All agent types should support reset."""
        agents = [
            RandomAgent(0),
            ThresholdAgent(1, threshold=50),
            ConservativeAgent(2),
            AggressiveAgent(3),
            SmartAgent(4),
            AdaptiveAgent(5),
        ]

        for agent in agents:
            agent.reset()  # Should not raise errors
