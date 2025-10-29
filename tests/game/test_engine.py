"""Integration tests for BANK! game engine.

These tests verify the full game flow and interactions between components.
Unit tests for specific functionality are in separate test modules:
- test_engine_initialization.py: Game setup and initialization
- test_engine_rounds.py: Round management
- test_engine_dice.py: Dice rolling mechanics
- test_engine_banking.py: Banking and accumulation rules
"""

from bank.game.engine import BankGame
from bank.game.state import GameState


class TestRoundTermination:
    """Integration tests for round ending conditions."""

    def test_is_round_over_no_round(self):
        """Test is_round_over when no round is active."""
        game = BankGame(num_players=2)
        assert game.is_round_over() is True

    def test_is_round_over_all_banked(self):
        """Test is_round_over when all players have banked."""
        game = BankGame(num_players=2)
        game.start_new_round()

        assert game.is_round_over() is False

        game.player_banks(0)
        game.player_banks(1)

        assert game.is_round_over() is True

    def test_is_round_over_seven_rolled(self):
        """Test is_round_over when seven ends the round."""
        game = BankGame(num_players=2)
        game.start_new_round()

        # Roll through first three
        game.roll_dice = lambda: (2, 2)
        for _ in range(3):
            game.process_roll()

        # Roll seven to end round
        game.roll_dice = lambda: (3, 4)
        game.process_roll()

        assert game.state.current_round.current_bank == 0
        assert game.is_round_over() is True


class TestGameEnd:
    """Integration tests for game ending conditions."""

    def test_game_ends_after_total_rounds(self):
        """Test that game ends after completing all rounds."""
        game = BankGame(num_players=2, total_rounds=2)

        # Round 1
        game.start_new_round()
        game.player_banks(0)
        game.player_banks(1)

        assert game.state.game_over is False

        # Round 2
        game.start_new_round()
        game.player_banks(0)
        game.player_banks(1)

        assert game.state.game_over is True

    def test_winner_determination(self):
        """Test that winner is player with highest score."""
        game = BankGame(num_players=2, total_rounds=1)
        game.start_new_round()

        # Give players different scores
        game.roll_dice = lambda: (5, 4)
        game.process_roll()  # Bank = 9

        game.state.players[0].score = 100
        game.player_banks(0)

        game.state.players[1].score = 150
        game.player_banks(1)

        assert game.state.game_over is True
        winner = game.get_winner()
        assert winner is not None
        assert winner.player_id == 1
        assert winner.score == 150 + 9


class TestGameReset:
    """Integration tests for game reset functionality."""

    def test_reset_clears_state(self):
        """Test that reset clears game state."""
        game = BankGame(num_players=2, player_names=["Alice", "Bob"])
        game.start_new_round()
        game.roll_dice = lambda: (3, 4)
        game.process_roll()
        game.player_banks(0)

        # Reset
        game.reset()

        assert game.state.current_round is None
        assert game.state.game_over is False
        assert game.state.winner is None
        assert all(p.score == 0 for p in game.state.players)
        assert all(not p.has_banked_this_round for p in game.state.players)

    def test_reset_with_seed(self):
        """Test that reset with seed makes game deterministic."""
        game = BankGame(num_players=2)

        game.reset(seed=42)
        rolls1 = [game.roll_dice() for _ in range(5)]

        game.reset(seed=42)
        rolls2 = [game.roll_dice() for _ in range(5)]

        assert rolls1 == rolls2

    def test_reset_preserves_players(self):
        """Test that reset preserves player names and count."""
        names = ["Alice", "Bob", "Charlie"]
        game = BankGame(num_players=3, player_names=names)

        game.reset()

        assert len(game.state.players) == 3
        assert [p.name for p in game.state.players] == names


class TestGetters:
    """Integration tests for getter methods."""

    def test_get_state(self):
        """Test get_state returns current GameState."""
        game = BankGame(num_players=2)
        state = game.get_state()

        assert isinstance(state, GameState)
        assert state == game.state

    def test_is_game_over(self):
        """Test is_game_over reflects game state."""
        game = BankGame(num_players=2)
        assert game.is_game_over() is False

        game.state.game_over = True
        assert game.is_game_over() is True

    def test_get_winner_before_game_over(self):
        """Test get_winner returns None before game ends."""
        game = BankGame(num_players=2)
        assert game.get_winner() is None

    def test_get_winner_after_game_over(self):
        """Test get_winner returns correct player."""
        game = BankGame(num_players=2, total_rounds=1)
        game.start_new_round()

        game.state.players[0].score = 100
        game.state.players[1].score = 50

        game.player_banks(0)
        game.player_banks(1)

        assert game.state.game_over is True
        winner = game.get_winner()
        assert winner is not None
        assert winner.name == "Player 1"
        assert winner.score >= 100

    def test_get_active_players(self):
        """Test get_active_players returns correct list."""
        game = BankGame(num_players=3)
        game.start_new_round()

        active = game.get_active_players()
        assert len(active) == 3

        game.player_banks(0)
        active = game.get_active_players()
        assert len(active) == 2

        game.player_banks(1)
        active = game.get_active_players()
        assert len(active) == 1
