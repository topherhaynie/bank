"""Tests for advanced strategic agents."""

from __future__ import annotations

import pytest

from bank.agents.advanced_agents import (
    LeaderOnlyAgent,
    LeaderPlusOneAgent,
    LeechAgent,
    RankBasedAgent,
)
from bank.agents.base import Observation
from bank.game.engine import BankGame


class TestLeaderOnlyAgent:
    """Tests for LeaderOnlyAgent."""

    def test_initialization(self) -> None:
        """Test agent initialization."""
        agent = LeaderOnlyAgent(player_id=0)
        assert agent.player_id == 0
        assert "LeaderOnly" in agent.name

        agent_custom = LeaderOnlyAgent(player_id=1, name="CustomLeader")
        assert agent_custom.name == "CustomLeader"

    def test_banks_when_becoming_leader(self) -> None:
        """Test agent banks when it would become the leader."""
        agent = LeaderOnlyAgent(player_id=0)

        # Scenario: player has 50, opponent has 60, bank is 15
        # After banking: player would have 65 > 60
        obs: Observation = {
            "round_number": 1,
            "roll_count": 3,
            "current_bank": 15,
            "last_roll": (4, 3),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 50,
            "can_bank": True,
            "all_player_scores": {0: 50, 1: 60},
        }

        assert agent.act(obs) == "bank"

    def test_does_not_bank_when_not_becoming_leader(self) -> None:
        """Test agent passes when banking wouldn't make it leader."""
        agent = LeaderOnlyAgent(player_id=0)

        # Scenario: player has 50, opponent has 80, bank is 15
        # After banking: player would have 65 < 80
        obs: Observation = {
            "round_number": 1,
            "roll_count": 3,
            "current_bank": 15,
            "last_roll": (4, 3),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 50,
            "can_bank": True,
            "all_player_scores": {0: 50, 1: 80},
        }

        assert agent.act(obs) == "pass"

    def test_respects_can_bank_constraint(self) -> None:
        """Test agent passes when can_bank is False."""
        agent = LeaderOnlyAgent(player_id=0)

        obs: Observation = {
            "round_number": 1,
            "roll_count": 3,
            "current_bank": 100,
            "last_roll": (5, 5),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 50,
            "can_bank": False,  # Already banked
            "all_player_scores": {0: 50, 1: 40},
        }

        assert agent.act(obs) == "pass"

    def test_banks_with_small_amount_when_already_leader(self) -> None:
        """Test agent banks even small amounts when already leading."""
        agent = LeaderOnlyAgent(player_id=0)

        # Already leading (100 > 80), bank is only 5
        obs: Observation = {
            "round_number": 1,
            "roll_count": 2,
            "current_bank": 5,
            "last_roll": (2, 3),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 100,
            "can_bank": True,
            "all_player_scores": {0: 100, 1: 80},
        }

        # Should bank because 105 > 80 (maintains lead)
        assert agent.act(obs) == "bank"


class TestLeaderPlusOneAgent:
    """Tests for LeaderPlusOneAgent."""

    def test_initialization(self) -> None:
        """Test agent initialization."""
        agent = LeaderPlusOneAgent(player_id=0)
        assert agent.player_id == 0
        assert "LeaderPlusOne" in agent.name

    def test_does_not_bank_on_first_roll(self) -> None:
        """Test agent waits at least one roll even when becoming leader."""
        agent = LeaderPlusOneAgent(player_id=0)

        # Would become leader but roll_count is 1
        obs: Observation = {
            "round_number": 1,
            "roll_count": 1,
            "current_bank": 20,
            "last_roll": (6, 6),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 50,
            "can_bank": True,
            "all_player_scores": {0: 50, 1: 60},
        }

        assert agent.act(obs) == "pass"

    def test_banks_after_waiting_when_becoming_leader(self) -> None:
        """Test agent banks after waiting when it would become leader."""
        agent = LeaderPlusOneAgent(player_id=0)

        # Roll 2+, would become leader
        obs: Observation = {
            "round_number": 1,
            "roll_count": 2,
            "current_bank": 20,
            "last_roll": (5, 4),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 50,
            "can_bank": True,
            "all_player_scores": {0: 50, 1: 60},
        }

        assert agent.act(obs) == "bank"

    def test_does_not_bank_when_not_leader_even_after_waiting(self) -> None:
        """Test agent still won't bank if not becoming leader."""
        agent = LeaderPlusOneAgent(player_id=0)

        # Waited (roll 3) but still wouldn't be leader
        obs: Observation = {
            "round_number": 1,
            "roll_count": 3,
            "current_bank": 15,
            "last_roll": (4, 3),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 50,
            "can_bank": True,
            "all_player_scores": {0: 50, 1: 80},
        }

        assert agent.act(obs) == "pass"


class TestLeechAgent:
    """Tests for LeechAgent."""

    def test_initialization(self) -> None:
        """Test agent initialization with custom parameters."""
        agent = LeechAgent(player_id=0)
        assert agent.player_id == 0
        assert agent.min_bank == 40
        assert agent.min_banked_players == 2

        agent_custom = LeechAgent(player_id=1, min_bank=50, min_banked_players=1)
        assert agent_custom.min_bank == 50
        assert agent_custom.min_banked_players == 1

    def test_banks_when_enough_players_banked(self) -> None:
        """Test agent banks when enough players have banked."""
        agent = LeechAgent(player_id=0, min_banked_players=2)

        # 4 total players, 2 active (0 and 1), so 2 have banked
        obs: Observation = {
            "round_number": 1,
            "roll_count": 5,
            "current_bank": 50,
            "last_roll": (3, 4),
            "active_player_ids": {0, 1},  # Only 2 still active
            "player_id": 0,
            "player_score": 100,
            "can_bank": True,
            "all_player_scores": {0: 100, 1: 90, 2: 110, 3: 95},
        }

        assert agent.act(obs) == "bank"

    def test_does_not_bank_when_too_few_banked(self) -> None:
        """Test agent waits when not enough players have banked."""
        agent = LeechAgent(player_id=0, min_banked_players=2)

        # 4 total, 3 active, only 1 has banked
        obs: Observation = {
            "round_number": 1,
            "roll_count": 3,
            "current_bank": 50,
            "last_roll": (3, 4),
            "active_player_ids": {0, 1, 2},  # 3 still active
            "player_id": 0,
            "player_score": 100,
            "can_bank": True,
            "all_player_scores": {0: 100, 1: 90, 2: 85, 3: 95},
        }

        assert agent.act(obs) == "pass"

    def test_does_not_bank_when_bank_too_low(self) -> None:
        """Test agent waits when bank value is below threshold."""
        agent = LeechAgent(player_id=0, min_bank=50)

        # Enough players banked but bank is only 30
        obs: Observation = {
            "round_number": 1,
            "roll_count": 4,
            "current_bank": 30,  # Below min_bank of 50
            "last_roll": (2, 3),
            "active_player_ids": {0, 1},
            "player_id": 0,
            "player_score": 100,
            "can_bank": True,
            "all_player_scores": {0: 100, 1: 90, 2: 110, 3: 95},
        }

        assert agent.act(obs) == "pass"


class TestRankBasedAgent:
    """Tests for RankBasedAgent."""

    def test_initialization(self) -> None:
        """Test agent initialization with custom thresholds."""
        agent = RankBasedAgent(player_id=0)
        assert agent.player_id == 0
        assert agent.leader_threshold == 40
        assert agent.middle_threshold == 60
        assert agent.last_threshold == 100

        agent_custom = RankBasedAgent(
            player_id=1,
            leader_threshold=30,
            middle_threshold=70,
            last_threshold=120,
        )
        assert agent_custom.leader_threshold == 30
        assert agent_custom.middle_threshold == 70
        assert agent_custom.last_threshold == 120

    def test_conservative_when_leading(self) -> None:
        """Test agent uses low threshold when in first place."""
        agent = RankBasedAgent(player_id=0, leader_threshold=40)

        # Player 0 is leading (150 > all others)
        obs: Observation = {
            "round_number": 1,
            "roll_count": 3,
            "current_bank": 45,  # Above leader threshold of 40
            "last_roll": (3, 4),
            "active_player_ids": {0, 1, 2, 3},
            "player_id": 0,
            "player_score": 150,
            "can_bank": True,
            "all_player_scores": {0: 150, 1: 120, 2: 110, 3: 100},
        }

        assert agent.act(obs) == "bank"

        # Below leader threshold
        obs["current_bank"] = 35
        assert agent.act(obs) == "pass"

    def test_aggressive_when_last(self) -> None:
        """Test agent uses high threshold when in last place."""
        agent = RankBasedAgent(player_id=0, last_threshold=100)

        # Player 0 is last (80 < all others)
        obs: Observation = {
            "round_number": 1,
            "roll_count": 4,
            "current_bank": 105,  # Above last threshold of 100
            "last_roll": (6, 5),
            "active_player_ids": {0, 1, 2, 3},
            "player_id": 0,
            "player_score": 80,
            "can_bank": True,
            "all_player_scores": {0: 80, 1: 120, 2: 150, 3: 100},
        }

        assert agent.act(obs) == "bank"

        # Below last threshold
        obs["current_bank"] = 95
        assert agent.act(obs) == "pass"

    def test_balanced_when_middle_rank(self) -> None:
        """Test agent uses medium threshold when in middle ranks."""
        agent = RankBasedAgent(player_id=0, middle_threshold=60)

        # Player 0 is rank 2 out of 4 (middle)
        obs: Observation = {
            "round_number": 1,
            "roll_count": 3,
            "current_bank": 65,  # Above middle threshold of 60
            "last_roll": (4, 3),
            "active_player_ids": {0, 1, 2, 3},
            "player_id": 0,
            "player_score": 120,
            "can_bank": True,
            "all_player_scores": {0: 120, 1: 100, 2: 150, 3: 130},
        }

        assert agent.act(obs) == "bank"

        # Below middle threshold
        obs["current_bank"] = 55
        assert agent.act(obs) == "pass"


class TestAdvancedAgentsIntegration:
    """Integration tests with game engine."""

    def test_all_advanced_agents_play_complete_game(self) -> None:
        """Test all advanced agents can play a complete game together."""
        agents = [
            LeaderOnlyAgent(0, "Leader"),
            LeaderPlusOneAgent(1, "LeaderPlus"),
            LeechAgent(2, "Leech"),
            RankBasedAgent(3, "RankBased"),
        ]

        game = BankGame(
            num_players=4,
            agents=agents,
            total_rounds=5,
        )

        # Should complete without errors
        game.play_game()

        assert game.state.game_over
        assert game.state.winner is not None

    def test_advanced_agents_make_decisions(self) -> None:
        """Test advanced agents make valid decisions during gameplay."""
        agents = [
            LeaderOnlyAgent(0),
            LeechAgent(1),
        ]

        game = BankGame(num_players=2, agents=agents, total_rounds=2)

        # Play complete game
        game.play_game()

        # Game should complete successfully
        assert game.state.game_over
        # Someone should have won
        assert game.state.winner is not None

    def test_leader_only_vs_rank_based_tournament(self) -> None:
        """Test LeaderOnly vs RankBased in a short tournament."""
        wins = {0: 0, 1: 0}

        for game_num in range(10):
            agents = [
                LeaderOnlyAgent(0, "LeaderOnly"),
                RankBasedAgent(1, "RankBased"),
            ]

            game = BankGame(
                num_players=2,
                agents=agents,
                total_rounds=5,
            )

            game.play_game()
            winner = game.get_winner()

            if winner:
                wins[winner.player_id] += 1

        # Both agents should win at least one game (probabilistic, but very likely)
        total_games = sum(wins.values())
        assert total_games == 10
        # At least one agent should have won something
        assert max(wins.values()) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
