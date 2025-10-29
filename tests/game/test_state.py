"""Tests for game state dataclasses."""

from bank.game.state import FIRST_THREE_ROLLS, GameState, PlayerState, RoundState


class TestPlayerState:
    """Tests for PlayerState dataclass."""

    def test_create_player_state(self):
        """Test creating a basic PlayerState."""
        player = PlayerState(player_id=1, name="Alice")
        assert player.player_id == 1
        assert player.name == "Alice"
        assert player.score == 0
        assert player.has_banked_this_round is False

    def test_player_state_with_score(self):
        """Test creating a PlayerState with a score."""
        player = PlayerState(player_id=2, name="Bob", score=100)
        assert player.score == 100

    def test_player_state_to_dict(self):
        """Test serializing PlayerState to dict."""
        player = PlayerState(
            player_id=1,
            name="Alice",
            score=50,
            has_banked_this_round=True,
        )
        data = player.to_dict()

        assert data == {
            "player_id": 1,
            "name": "Alice",
            "score": 50,
            "has_banked_this_round": True,
        }

    def test_player_state_from_dict(self):
        """Test deserializing PlayerState from dict."""
        data = {
            "player_id": 2,
            "name": "Bob",
            "score": 75,
            "has_banked_this_round": False,
        }
        player = PlayerState.from_dict(data)

        assert player.player_id == 2
        assert player.name == "Bob"
        assert player.score == 75
        assert player.has_banked_this_round is False

    def test_player_state_roundtrip(self):
        """Test that to_dict/from_dict roundtrip preserves state."""
        original = PlayerState(
            player_id=3,
            name="Charlie",
            score=120,
            has_banked_this_round=True,
        )

        data = original.to_dict()
        restored = PlayerState.from_dict(data)

        assert restored.player_id == original.player_id
        assert restored.name == original.name
        assert restored.score == original.score
        assert restored.has_banked_this_round == original.has_banked_this_round

    def test_player_state_repr(self):
        """Test string representation of PlayerState."""
        player = PlayerState(player_id=1, name="Alice", score=50)
        repr_str = repr(player)
        assert "Alice" in repr_str
        assert "50" in repr_str


class TestRoundState:
    """Tests for RoundState dataclass."""

    def test_create_round_state(self):
        """Test creating a basic RoundState."""
        round_state = RoundState(round_number=1)
        assert round_state.round_number == 1
        assert round_state.roll_count == 0
        assert round_state.current_bank == 0
        assert round_state.last_roll is None
        assert len(round_state.active_player_ids) == 0

    def test_round_state_with_roll(self):
        """Test RoundState with a dice roll."""
        round_state = RoundState(
            round_number=2,
            roll_count=1,
            current_bank=8,
            last_roll=(3, 5),
            active_player_ids={1, 2, 3},
        )
        assert round_state.last_roll == (3, 5)
        assert round_state.current_bank == 8
        assert len(round_state.active_player_ids) == 3

    def test_round_state_to_dict(self):
        """Test serializing RoundState to dict."""
        round_state = RoundState(
            round_number=3,
            roll_count=2,
            current_bank=15,
            last_roll=(4, 3),
            active_player_ids={1, 2},
        )
        data = round_state.to_dict()

        assert data["round_number"] == 3
        assert data["roll_count"] == 2
        assert data["current_bank"] == 15
        assert data["last_roll"] == [4, 3]
        assert set(data["active_player_ids"]) == {1, 2}

    def test_round_state_to_dict_no_roll(self):
        """Test serializing RoundState with no roll yet."""
        round_state = RoundState(round_number=1)
        data = round_state.to_dict()

        assert data["last_roll"] is None
        assert data["active_player_ids"] == []

    def test_round_state_from_dict(self):
        """Test deserializing RoundState from dict."""
        data = {
            "round_number": 5,
            "roll_count": 4,
            "current_bank": 42,
            "last_roll": [6, 1],
            "active_player_ids": [1, 3, 4],
        }
        round_state = RoundState.from_dict(data)

        assert round_state.round_number == 5
        assert round_state.roll_count == 4
        assert round_state.current_bank == 42
        assert round_state.last_roll == (6, 1)
        assert round_state.active_player_ids == {1, 3, 4}

    def test_round_state_from_dict_no_roll(self):
        """Test deserializing RoundState with no roll."""
        data = {
            "round_number": 1,
            "roll_count": 0,
            "current_bank": 0,
            "last_roll": None,
            "active_player_ids": [1, 2, 3],
        }
        round_state = RoundState.from_dict(data)

        assert round_state.last_roll is None
        assert round_state.active_player_ids == {1, 2, 3}

    def test_round_state_roundtrip(self):
        """Test that to_dict/from_dict roundtrip preserves state."""
        original = RoundState(
            round_number=7,
            roll_count=10,
            current_bank=250,
            last_roll=(5, 5),
            active_player_ids={2, 4},
        )

        data = original.to_dict()
        restored = RoundState.from_dict(data)

        assert restored.round_number == original.round_number
        assert restored.roll_count == original.roll_count
        assert restored.current_bank == original.current_bank
        assert restored.last_roll == original.last_roll
        assert restored.active_player_ids == original.active_player_ids

    def test_is_first_three_rolls(self):
        """Test the is_first_three_rolls helper method."""
        round_state = RoundState(round_number=1)

        # Roll 0 (no rolls yet) - not in first 3
        assert round_state.is_first_three_rolls() is False

        # Rolls 1-3 should be first three rolls
        for roll_count in range(1, FIRST_THREE_ROLLS + 1):
            round_state.roll_count = roll_count
            assert round_state.is_first_three_rolls() is True, f"Roll {roll_count} should be in first three"

        # Roll 4 and beyond should not be first three rolls
        for roll_count in range(FIRST_THREE_ROLLS + 1, 10):
            round_state.roll_count = roll_count
            assert round_state.is_first_three_rolls() is False, f"Roll {roll_count} should not be in first three"

    def test_round_state_repr(self):
        """Test string representation of RoundState."""
        round_state = RoundState(
            round_number=3,
            roll_count=5,
            current_bank=100,
            active_player_ids={1, 2},
        )
        repr_str = repr(round_state)
        assert "3" in repr_str  # round number
        assert "5" in repr_str  # roll count
        assert "100" in repr_str  # bank


class TestGameState:
    """Tests for GameState dataclass."""

    def test_create_game_state(self):
        """Test creating a basic GameState."""
        players = [
            PlayerState(player_id=1, name="Alice"),
            PlayerState(player_id=2, name="Bob"),
        ]
        game = GameState(players=players)

        assert len(game.players) == 2
        assert game.total_rounds == 10
        assert game.current_round is None
        assert game.game_over is False
        assert game.winner is None

    def test_game_state_custom_rounds(self):
        """Test creating a GameState with custom round count."""
        players = [PlayerState(player_id=1, name="Alice")]
        game = GameState(players=players, total_rounds=20)
        assert game.total_rounds == 20

    def test_num_players_property(self):
        """Test the num_players property."""
        players = [PlayerState(player_id=i, name=f"Player{i}") for i in range(4)]
        game = GameState(players=players)
        assert game.num_players == 4

    def test_get_player(self):
        """Test getting a player by ID."""
        players = [
            PlayerState(player_id=1, name="Alice"),
            PlayerState(player_id=2, name="Bob"),
            PlayerState(player_id=3, name="Charlie"),
        ]
        game = GameState(players=players)

        alice = game.get_player(1)
        assert alice is not None
        assert alice.name == "Alice"

        bob = game.get_player(2)
        assert bob is not None
        assert bob.name == "Bob"

        # Non-existent player
        nobody = game.get_player(99)
        assert nobody is None

    def test_get_active_players_no_round(self):
        """Test get_active_players when no round is active."""
        players = [PlayerState(player_id=1, name="Alice")]
        game = GameState(players=players)

        active = game.get_active_players()
        assert active == []

    def test_get_active_players_with_round(self):
        """Test get_active_players during an active round."""
        players = [
            PlayerState(player_id=1, name="Alice"),
            PlayerState(player_id=2, name="Bob"),
            PlayerState(player_id=3, name="Charlie"),
        ]
        game = GameState(
            players=players,
            current_round=RoundState(
                round_number=1,
                active_player_ids={1, 3},
            ),
        )

        active = game.get_active_players()
        assert len(active) == 2
        assert any(p.name == "Alice" for p in active)
        assert any(p.name == "Charlie" for p in active)
        assert not any(p.name == "Bob" for p in active)

    def test_get_leading_player_empty(self):
        """Test get_leading_player with no players."""
        game = GameState(players=[])
        assert game.get_leading_player() is None

    def test_get_leading_player(self):
        """Test get_leading_player returns player with highest score."""
        players = [
            PlayerState(player_id=1, name="Alice", score=50),
            PlayerState(player_id=2, name="Bob", score=100),
            PlayerState(player_id=3, name="Charlie", score=75),
        ]
        game = GameState(players=players)

        leader = game.get_leading_player()
        assert leader is not None
        assert leader.name == "Bob"
        assert leader.score == 100

    def test_game_state_to_dict(self):
        """Test serializing GameState to dict."""
        players = [
            PlayerState(player_id=1, name="Alice", score=50),
            PlayerState(player_id=2, name="Bob", score=75),
        ]
        round_state = RoundState(
            round_number=3,
            roll_count=2,
            current_bank=30,
            active_player_ids={1, 2},
        )
        game = GameState(
            players=players,
            total_rounds=15,
            current_round=round_state,
            game_over=False,
            winner=None,
        )

        data = game.to_dict()

        assert len(data["players"]) == 2
        assert data["total_rounds"] == 15
        assert data["current_round"]["round_number"] == 3
        assert data["game_over"] is False
        assert data["winner"] is None

    def test_game_state_to_dict_no_round(self):
        """Test serializing GameState with no active round."""
        players = [PlayerState(player_id=1, name="Alice")]
        game = GameState(players=players)

        data = game.to_dict()
        assert data["current_round"] is None

    def test_game_state_to_dict_with_winner(self):
        """Test serializing GameState with a winner."""
        players = [PlayerState(player_id=1, name="Alice", score=200)]
        game = GameState(
            players=players,
            game_over=True,
            winner=1,
        )

        data = game.to_dict()
        assert data["game_over"] is True
        assert data["winner"] == 1

    def test_game_state_from_dict(self):
        """Test deserializing GameState from dict."""
        data = {
            "players": [
                {"player_id": 1, "name": "Alice", "score": 100, "has_banked_this_round": False},
                {"player_id": 2, "name": "Bob", "score": 150, "has_banked_this_round": True},
            ],
            "total_rounds": 20,
            "current_round": {
                "round_number": 5,
                "roll_count": 3,
                "current_bank": 45,
                "last_roll": [2, 4],
                "active_player_ids": [1],
            },
            "game_over": False,
            "winner": None,
        }

        game = GameState.from_dict(data)

        assert game.num_players == 2
        assert game.players[0].name == "Alice"
        assert game.players[1].name == "Bob"
        assert game.total_rounds == 20
        assert game.current_round is not None
        assert game.current_round.round_number == 5
        assert game.game_over is False
        assert game.winner is None

    def test_game_state_from_dict_no_round(self):
        """Test deserializing GameState with no active round."""
        data = {
            "players": [
                {"player_id": 1, "name": "Alice", "score": 0, "has_banked_this_round": False},
            ],
            "total_rounds": 10,
            "current_round": None,
            "game_over": False,
            "winner": None,
        }

        game = GameState.from_dict(data)
        assert game.current_round is None

    def test_game_state_roundtrip(self):
        """Test that to_dict/from_dict roundtrip preserves state."""
        original = GameState(
            players=[
                PlayerState(player_id=1, name="Alice", score=120, has_banked_this_round=True),
                PlayerState(player_id=2, name="Bob", score=95, has_banked_this_round=False),
            ],
            total_rounds=15,
            current_round=RoundState(
                round_number=8,
                roll_count=5,
                current_bank=180,
                last_roll=(6, 6),
                active_player_ids={2},
            ),
            game_over=False,
            winner=None,
        )

        data = original.to_dict()
        restored = GameState.from_dict(data)

        assert restored.num_players == original.num_players
        assert restored.total_rounds == original.total_rounds
        assert restored.game_over == original.game_over
        assert restored.winner == original.winner

        # Check players
        for orig_player, rest_player in zip(original.players, restored.players):
            assert rest_player.player_id == orig_player.player_id
            assert rest_player.name == orig_player.name
            assert rest_player.score == orig_player.score
            assert rest_player.has_banked_this_round == orig_player.has_banked_this_round

        # Check round state
        assert restored.current_round is not None
        assert restored.current_round.round_number == original.current_round.round_number
        assert restored.current_round.roll_count == original.current_round.roll_count
        assert restored.current_round.current_bank == original.current_round.current_bank
        assert restored.current_round.last_roll == original.current_round.last_roll
        assert restored.current_round.active_player_ids == original.current_round.active_player_ids

    def test_game_state_repr(self):
        """Test string representation of GameState."""
        players = [PlayerState(player_id=1, name="Alice")]

        # Game not started
        game = GameState(players=players)
        repr_str = repr(game)
        assert "not started" in repr_str

        # Game in progress
        game.current_round = RoundState(round_number=3)
        repr_str = repr(game)
        assert "3" in repr_str
        assert "10" in repr_str  # total rounds
