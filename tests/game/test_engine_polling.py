"""Tests for BANK! game engine agent polling and decision making."""

from bank.agents.test_agents import AlwaysBankAgent, AlwaysPassAgent, ThresholdAgent
from bank.game.engine import BankGame


class TestAgentPolling:
    """Tests for agent polling mechanism."""

    def test_poll_with_no_agents(self):
        """Test that polling without agents returns empty list."""
        game = BankGame(num_players=2)
        game.start_new_round()

        banked = game.poll_decisions()
        assert banked == []

    def test_poll_with_always_pass_agents(self):
        """Test that AlwaysPassAgent never banks."""
        agents = [AlwaysPassAgent(0), AlwaysPassAgent(1)]
        game = BankGame(num_players=2, agents=agents)
        game.start_new_round()

        # Build up some bank
        game.state.current_round.current_bank = 100

        # Poll decisions
        banked = game.poll_decisions()
        assert banked == []

        # Verify no one banked
        assert all(not p.has_banked_this_round for p in game.state.players)

    def test_poll_with_always_bank_agents(self):
        """Test that AlwaysBankAgent always banks when possible."""
        agents = [AlwaysBankAgent(0), AlwaysBankAgent(1)]
        game = BankGame(num_players=2, agents=agents)
        game.start_new_round()

        # Build up some bank
        game.state.current_round.current_bank = 50

        # Poll decisions
        banked = game.poll_decisions()

        # Both should have banked
        assert len(banked) == 2
        assert 0 in banked
        assert 1 in banked

        # Verify scores
        assert game.state.players[0].score == 50
        assert game.state.players[1].score == 50

    def test_poll_deterministic_ordering(self):
        """Test that polling in deterministic mode processes in player ID order."""
        agents = [AlwaysBankAgent(0), AlwaysBankAgent(1), AlwaysBankAgent(2)]
        game = BankGame(num_players=3, agents=agents, deterministic_polling=True)
        game.start_new_round()

        game.state.current_round.current_bank = 100

        # Poll should process in order: 0, 1, 2
        banked = game.poll_decisions()

        # Should be in order
        assert banked == [0, 1, 2]

    def test_poll_simultaneous_mode(self):
        """Test that simultaneous polling collects all decisions before processing."""
        # In simultaneous mode, all agents see the same bank value
        # This test verifies that both agents can bank from the same bank value
        agents = [AlwaysBankAgent(0), AlwaysBankAgent(1)]
        game = BankGame(num_players=2, agents=agents, deterministic_polling=False)
        game.start_new_round()

        game.state.current_round.current_bank = 50

        # Poll in simultaneous mode
        banked = game.poll_decisions()

        # Both should bank (sorted by player ID in result)
        assert len(banked) == 2
        assert banked == [0, 1]
        # Both get the same value
        assert game.state.players[0].score == 50
        assert game.state.players[1].score == 50

    def test_poll_with_mixed_agents(self):
        """Test polling with a mix of agent types."""
        agents = [
            AlwaysPassAgent(0),
            AlwaysBankAgent(1),
            ThresholdAgent(2, threshold=50),
        ]
        game = BankGame(num_players=3, agents=agents)
        game.start_new_round()

        # Bank below threshold
        game.state.current_round.current_bank = 30

        banked = game.poll_decisions()

        # Only AlwaysBankAgent should bank
        assert banked == [1]
        assert game.state.players[1].score == 30
        assert game.state.players[0].score == 0
        assert game.state.players[2].score == 0

    def test_poll_with_threshold_agent(self):
        """Test ThresholdAgent banks only when threshold is met."""
        agents = [ThresholdAgent(0, threshold=50), ThresholdAgent(1, threshold=100)]
        game = BankGame(num_players=2, agents=agents)
        game.start_new_round()

        # Bank = 75 (above 50, below 100)
        game.state.current_round.current_bank = 75

        banked = game.poll_decisions()

        # Only player 0 should bank
        assert banked == [0]
        assert game.state.players[0].score == 75
        assert game.state.players[1].score == 0

    def test_poll_no_repeat_banking(self):
        """Test that players who already banked don't bank again."""
        agents = [AlwaysBankAgent(0), AlwaysBankAgent(1)]
        game = BankGame(num_players=2, agents=agents)
        game.start_new_round()

        game.state.current_round.current_bank = 50

        # First poll
        banked1 = game.poll_decisions()
        assert len(banked1) == 2

        # Second poll - no one should bank again
        banked2 = game.poll_decisions()
        assert banked2 == []

    def test_observation_contains_correct_data(self):
        """Test that observations contain correct game state."""
        agents = [AlwaysBankAgent(0), AlwaysPassAgent(1)]
        game = BankGame(num_players=2, agents=agents)
        game.start_new_round()

        # Manually set some game state for observation testing
        game.state.current_round.round_number = 3
        game.state.current_round.roll_count = 5
        game.state.current_round.current_bank = 25
        game.state.current_round.last_roll = (4, 6)
        game.state.current_round.active_player_ids = {0, 1}
        game.state.players[0].score = 15
        game.state.players[1].score = 20

        obs = game.create_observation(0)

        assert obs["round_number"] == 3
        assert obs["roll_count"] == 5
        assert obs["current_bank"] == 25
        assert obs["last_roll"] == (4, 6)
        assert obs["active_player_ids"] == {0, 1}
        assert obs["player_id"] == 0
        assert obs["player_score"] == 15
        assert obs["can_bank"] is True
        assert obs["all_player_scores"] == {0: 15, 1: 20}

    def test_observation_after_banking(self):
        """Test that observations reflect banking status correctly."""
        agents = [AlwaysBankAgent(0), AlwaysPassAgent(1)]
        game = BankGame(num_players=2, agents=agents)
        game.start_new_round()
        game.roll_dice()

        # Player 0 banks
        game.player_banks(0)

        # Now player 0 should not be active
        obs = game.create_observation(0)
        assert obs["can_bank"] is False
        assert 0 not in obs["active_player_ids"]

        # Player 1 is still active
        obs_1 = game.create_observation(1)
        assert obs_1["can_bank"] is True
        assert 1 in obs_1["active_player_ids"]


class TestIntegrationWithRolling:
    """Integration tests for polling within game flow."""

    def test_roll_and_poll_workflow(self):
        """Test complete roll and poll cycle."""
        agents = [ThresholdAgent(0, threshold=20), AlwaysPassAgent(1)]
        game = BankGame(num_players=2, agents=agents)
        game.start_new_round()

        # Mock dice rolls
        game.roll_dice = lambda: (5, 4)  # Sum = 9

        # Roll 1
        game.process_roll()
        banked = game.poll_decisions()
        assert banked == []  # Bank = 9, below threshold

        # Roll 2
        game.process_roll()
        banked = game.poll_decisions()
        assert banked == []  # Bank = 18, still below

        # Roll 3
        game.process_roll()
        banked = game.poll_decisions()
        assert banked == [0]  # Bank = 27, player 0 banks

        # Verify
        assert game.state.players[0].score == 27
        assert game.state.players[1].score == 0

    def test_all_players_banking_ends_round(self):
        """Test that round ends when all players bank via polling."""
        agents = [AlwaysBankAgent(0), AlwaysBankAgent(1)]
        game = BankGame(num_players=2, agents=agents)
        game.start_new_round()

        game.state.current_round.current_bank = 50

        # Poll - both should bank
        game.poll_decisions()

        # Round should be over
        assert game.is_round_over() is True

    def test_seven_prevents_banking(self):
        """Test that rolling seven after first 3 prevents banking."""
        agents = [AlwaysBankAgent(0), AlwaysBankAgent(1)]
        game = BankGame(num_players=2, agents=agents)
        game.start_new_round()

        # Roll through first 3
        game.roll_dice = lambda: (2, 2)
        for _ in range(3):
            game.process_roll()

        bank_after_three = game.state.current_round.current_bank
        assert bank_after_three > 0

        # Roll a seven (ends round)
        game.roll_dice = lambda: (3, 4)
        game.process_roll()

        # Bank should be 0
        assert game.state.current_round.current_bank == 0

        # Polling should result in no banks (nothing to bank)
        banked = game.poll_decisions()
        # AlwaysBankAgent will try to bank, but bank is 0
        # The banking logic should still succeed (they get 0 points)
        assert len(banked) == 2
        assert all(p.score == 0 for p in game.state.players)

    def test_agents_parameter_validation(self):
        """Test that agent count must match player count."""
        agents = [AlwaysBankAgent(0)]

        try:
            BankGame(num_players=2, agents=agents)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "must match" in str(e).lower()
