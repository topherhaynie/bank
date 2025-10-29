"""Tests for BANK! game engine banking mechanics."""

from bank.game.engine import BankGame


class TestBankAccumulation:
    """Tests for bank accumulation rules."""

    def test_seven_in_first_three_rolls_adds_70(self):
        """Test that rolling seven in first 3 rolls adds 70 to bank."""
        game = BankGame(num_players=2)
        game.start_new_round()

        # Mock roll to force a 7
        game.roll_dice = lambda: (3, 4)  # Sum = 7
        game.process_roll()

        assert game.state.current_round.current_bank == 70

    def test_seven_after_three_rolls_ends_round(self):
        """Test that rolling seven after first 3 rolls ends the round."""
        game = BankGame(num_players=2)
        game.start_new_round()

        # Roll through first 3
        game.roll_dice = lambda: (2, 3)
        for _ in range(3):
            game.process_roll()

        bank_before = game.state.current_round.current_bank
        assert bank_before > 0

        # Roll a 7
        game.roll_dice = lambda: (4, 3)  # Sum = 7
        game.process_roll()

        assert game.state.current_round.current_bank == 0

    def test_doubles_in_first_three_rolls_adds_sum(self):
        """Test that rolling doubles in first 3 rolls adds the sum."""
        game = BankGame(num_players=2)
        game.start_new_round()

        game.roll_dice = lambda: (4, 4)  # Doubles, sum = 8
        game.process_roll()

        assert game.state.current_round.current_bank == 8

    def test_doubles_after_three_rolls_doubles_bank(self):
        """Test that rolling doubles after first 3 rolls doubles the bank."""
        game = BankGame(num_players=2)
        game.start_new_round()

        # Build up bank with 3 normal rolls
        game.roll_dice = lambda: (2, 3)
        for _ in range(3):
            game.process_roll()

        bank_before = game.state.current_round.current_bank
        assert bank_before > 0

        # Roll doubles
        game.roll_dice = lambda: (5, 5)
        game.process_roll()

        assert game.state.current_round.current_bank == bank_before * 2

    def test_normal_roll_adds_sum(self):
        """Test that normal rolls add the sum to the bank."""
        game = BankGame(num_players=2)
        game.start_new_round()

        game.roll_dice = lambda: (3, 5)  # Sum = 8, not doubles or seven
        game.process_roll()

        assert game.state.current_round.current_bank == 8


class TestPlayerBanking:
    """Tests for player banking actions."""

    def test_player_banks_successfully(self):
        """Test that a player can successfully bank."""
        game = BankGame(num_players=2)
        game.start_new_round()

        # Build up bank
        game.state.current_round.current_bank = 100

        # Player 0 banks
        result = game.player_banks(0)

        assert result is True
        assert game.state.players[0].score == 100
        assert game.state.players[0].has_banked_this_round

    def test_player_banking_removes_from_active(self):
        """Test that banking removes player from active list."""
        game = BankGame(num_players=3)
        game.start_new_round()

        game.state.current_round.current_bank = 50

        # Player 1 banks
        game.player_banks(1)

        assert 1 not in game.state.current_round.active_player_ids
        assert len(game.state.current_round.active_player_ids) == 2

    def test_round_ends_when_all_players_bank(self):
        """Test that round ends when all players have banked."""
        game = BankGame(num_players=2)
        game.start_new_round()

        game.state.current_round.current_bank = 100

        # Both players bank
        game.player_banks(0)
        game.player_banks(1)

        assert game.is_round_over()

    def test_player_banking_with_zero_bank(self):
        """Test that player can bank even with zero in the bank."""
        game = BankGame(num_players=2)
        game.start_new_round()

        # Player can bank with zero (they just get 0 points)
        result = game.player_banks(0)
        assert result is True
        assert game.state.players[0].score == 0

    def test_player_banking_twice_same_round(self):
        """Test that player cannot bank twice in the same round."""
        game = BankGame(num_players=2)
        game.start_new_round()

        game.state.current_round.current_bank = 100
        game.player_banks(0)

        # Try to bank again - should fail
        result = game.player_banks(0)
        assert result is False
