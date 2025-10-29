"""Tests for BANK! game engine initialization."""

import random

import pytest

from bank.game.engine import BankGame


class TestGameInitialization:
    """Tests for game initialization and setup."""

    def test_game_initialization_basic(self):
        """Test that game initializes correctly with defaults."""
        game = BankGame(num_players=2)

        assert game.state.num_players == 2
        assert len(game.state.players) == 2
        assert game.state.total_rounds == 10
        assert game.state.current_round is None
        assert not game.state.game_over
        assert game.state.winner is None

    def test_game_initialization_custom_names(self):
        """Test game initialization with custom player names."""
        names = ["Alice", "Bob", "Charlie"]
        game = BankGame(num_players=3, player_names=names)

        assert game.state.players[0].name == "Alice"
        assert game.state.players[1].name == "Bob"
        assert game.state.players[2].name == "Charlie"

    def test_game_initialization_custom_rounds(self):
        """Test game initialization with custom round count."""
        game = BankGame(num_players=2, total_rounds=15)
        assert game.state.total_rounds == 15

    def test_game_initialization_with_rng(self):
        """Test game initialization with custom RNG for determinism."""
        rng = random.Random(42)
        game = BankGame(num_players=2, rng=rng)
        assert game.rng == rng

    def test_game_initialization_min_players_error(self):
        """Test that initialization fails with too few players."""
        with pytest.raises(ValueError, match="at least"):
            BankGame(num_players=1)

    def test_game_initialization_name_count_mismatch(self):
        """Test that initialization fails when name count doesn't match player count."""
        with pytest.raises(ValueError, match="must match"):
            BankGame(num_players=3, player_names=["Alice", "Bob"])

    def test_player_ids_sequential(self):
        """Test that player IDs are assigned sequentially."""
        game = BankGame(num_players=4)
        for i, player in enumerate(game.state.players):
            assert player.player_id == i

    def test_initial_player_scores_zero(self):
        """Test that all players start with zero score."""
        game = BankGame(num_players=3)
        for player in game.state.players:
            assert player.score == 0
            assert not player.has_banked_this_round
