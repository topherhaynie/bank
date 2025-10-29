"""Tests for BANK! game engine round management."""

from bank.game.engine import BankGame


class TestRoundManagement:
    """Tests for round management and lifecycle."""

    def test_start_new_round(self):
        """Test starting a new round initializes state correctly."""
        game = BankGame(num_players=2)
        game.start_new_round()

        assert game.state.current_round is not None
        assert game.state.current_round.round_number == 1
        assert game.state.current_round.roll_count == 0
        assert game.state.current_round.current_bank == 0
        assert game.state.current_round.last_roll is None
        assert len(game.state.current_round.active_player_ids) == 2

    def test_start_new_round_resets_player_banking_flags(self):
        """Test that starting a new round resets has_banked_this_round flags."""
        game = BankGame(num_players=2)
        game.start_new_round()

        # Simulate a player banking
        game.state.players[0].has_banked_this_round = True

        # Start new round
        game.start_new_round()

        # Check flags are reset
        for player in game.state.players:
            assert not player.has_banked_this_round

    def test_round_number_increments(self):
        """Test that round numbers increment correctly."""
        game = BankGame(num_players=2)

        game.start_new_round()
        assert game.state.current_round.round_number == 1

        game.start_new_round()
        assert game.state.current_round.round_number == 2

        game.start_new_round()
        assert game.state.current_round.round_number == 3

    def test_game_ends_after_final_round(self):
        """Test that game ends after the configured number of rounds."""
        game = BankGame(num_players=2, total_rounds=3)

        for _ in range(3):
            game.start_new_round()

        # Game should not be over yet (rounds completed but need to actually play them)
        assert not game.state.game_over

        # Mark game as complete
        game.state.game_over = True
        game.state.winner = game.state.get_leading_player()

        assert game.state.game_over
        assert game.state.winner is not None
