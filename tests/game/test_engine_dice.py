"""Tests for BANK! game engine dice rolling."""

import random

from bank.game.engine import BankGame


class TestDiceRolling:
    """Tests for dice rolling mechanics."""

    def test_roll_dice_returns_valid_values(self):
        """Test that roll_dice returns values in valid range."""
        game = BankGame(num_players=2)

        for _ in range(100):  # Test multiple rolls
            die1, die2 = game.roll_dice()
            assert 1 <= die1 <= 6
            assert 1 <= die2 <= 6

    def test_roll_dice_with_seeded_rng(self):
        """Test that dice rolls are deterministic with seeded RNG."""
        rng1 = random.Random(42)
        game1 = BankGame(num_players=2, rng=rng1)

        rng2 = random.Random(42)
        game2 = BankGame(num_players=2, rng=rng2)

        # Both games should produce identical sequences
        for _ in range(10):
            roll1 = game1.roll_dice()
            roll2 = game2.roll_dice()
            assert roll1 == roll2
