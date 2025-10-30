"""Tests for the GameRecorder class and replay save/load functionality."""

import tempfile
from pathlib import Path

import pytest

from bank.replay.recorder import GameRecorder, load_replay, save_replay


class TestGameRecorder:
    """Tests for the GameRecorder class."""

    def test_initialization(self) -> None:
        """Test that recorder initializes with empty state."""
        recorder = GameRecorder()
        assert recorder.events == []
        assert recorder.metadata == {}

    def test_start_game(self) -> None:
        """Test recording game start event."""
        recorder = GameRecorder()
        recorder.start_game(
            num_players=4,
            player_names=["Alice", "Bob", "Charlie", "Diana"],
            total_rounds=10,
            seed=42,
        )

        assert len(recorder.events) == 1
        event = recorder.events[0]
        assert event["type"] == "game_start"
        assert event["data"]["num_players"] == 4
        assert event["data"]["player_names"] == ["Alice", "Bob", "Charlie", "Diana"]
        assert event["data"]["total_rounds"] == 10
        assert event["data"]["seed"] == 42
        assert "timestamp" in event

        # Check metadata
        assert recorder.metadata["num_players"] == 4
        assert recorder.metadata["player_names"] == ["Alice", "Bob", "Charlie", "Diana"]
        assert recorder.metadata["total_rounds"] == 10

    def test_record_round_start(self) -> None:
        """Test recording round start event."""
        recorder = GameRecorder()
        recorder.record_round_start(round_number=3)

        assert len(recorder.events) == 1
        event = recorder.events[0]
        assert event["type"] == "round_start"
        assert event["data"]["round_number"] == 3
        assert "timestamp" in event

    def test_record_roll(self) -> None:
        """Test recording roll event."""
        recorder = GameRecorder()
        recorder.record_roll(
            round_number=2,
            roll_count=5,
            dice=(3, 4),
            bank_before=50,
            bank_after=57,
        )

        assert len(recorder.events) == 1
        event = recorder.events[0]
        assert event["type"] == "roll"
        assert event["data"]["round_number"] == 2
        assert event["data"]["roll_count"] == 5
        assert event["data"]["dice"] == [3, 4]
        assert event["data"]["bank_before"] == 50
        assert event["data"]["bank_after"] == 57
        assert "timestamp" in event

    def test_record_roll_with_seven(self) -> None:
        """Test recording a roll that results in seven."""
        recorder = GameRecorder()
        recorder.record_roll(
            round_number=1,
            roll_count=4,
            dice=(3, 4),
            bank_before=100,
            bank_after=0,  # Seven rolled, bank lost
        )

        event = recorder.events[0]
        assert event["data"]["dice"] == [3, 4]
        assert sum(event["data"]["dice"]) == 7
        assert event["data"]["bank_after"] == 0

    def test_record_roll_with_doubles(self) -> None:
        """Test recording a roll with doubles."""
        recorder = GameRecorder()
        recorder.record_roll(
            round_number=1,
            roll_count=4,
            dice=(5, 5),
            bank_before=50,
            bank_after=100,  # Doubles after first 3 rolls
        )

        event = recorder.events[0]
        assert event["data"]["dice"] == [5, 5]
        assert event["data"]["dice"][0] == event["data"]["dice"][1]

    def test_record_bank(self) -> None:
        """Test recording bank event."""
        recorder = GameRecorder()
        recorder.record_bank(
            round_number=2,
            player_id=1,
            player_name="Bob",
            amount=75,
            score_before=100,
            score_after=175,
        )

        assert len(recorder.events) == 1
        event = recorder.events[0]
        assert event["type"] == "bank"
        assert event["data"]["round_number"] == 2
        assert event["data"]["player_id"] == 1
        assert event["data"]["player_name"] == "Bob"
        assert event["data"]["amount"] == 75
        assert event["data"]["score_before"] == 100
        assert event["data"]["score_after"] == 175
        assert "timestamp" in event

    def test_record_round_end_seven_rolled(self) -> None:
        """Test recording round end due to seven."""
        recorder = GameRecorder()
        recorder.record_round_end(
            round_number=3,
            reason="seven_rolled",
            final_bank=0,
            player_scores={0: 100, 1: 150, 2: 75, 3: 90},
        )

        assert len(recorder.events) == 1
        event = recorder.events[0]
        assert event["type"] == "round_end"
        assert event["data"]["round_number"] == 3
        assert event["data"]["reason"] == "seven_rolled"
        assert event["data"]["final_bank"] == 0
        assert event["data"]["player_scores"] == {0: 100, 1: 150, 2: 75, 3: 90}
        assert "timestamp" in event

    def test_record_round_end_all_banked(self) -> None:
        """Test recording round end when all players banked."""
        recorder = GameRecorder()
        recorder.record_round_end(
            round_number=1,
            reason="all_banked",
            final_bank=50,
            player_scores={0: 120, 1: 100},
        )

        event = recorder.events[0]
        assert event["data"]["reason"] == "all_banked"
        assert event["data"]["final_bank"] == 50

    def test_record_game_end(self) -> None:
        """Test recording game end event."""
        recorder = GameRecorder()
        recorder.record_game_end(
            final_scores={0: 300, 1: 275, 2: 325, 3: 280},
            winner_ids=[2],
            winner_names=["Charlie"],
        )

        assert len(recorder.events) == 1
        event = recorder.events[0]
        assert event["type"] == "game_end"
        assert event["data"]["final_scores"] == {0: 300, 1: 275, 2: 325, 3: 280}
        assert event["data"]["winner_ids"] == [2]
        assert event["data"]["winner_names"] == ["Charlie"]
        assert "timestamp" in event

    def test_record_game_end_tie(self) -> None:
        """Test recording game end with a tie."""
        recorder = GameRecorder()
        recorder.record_game_end(
            final_scores={0: 300, 1: 300},
            winner_ids=[0, 1],
            winner_names=["Alice", "Bob"],
        )

        event = recorder.events[0]
        assert event["data"]["winner_ids"] == [0, 1]
        assert event["data"]["winner_names"] == ["Alice", "Bob"]

    def test_to_dict(self) -> None:
        """Test converting recorder to dictionary."""
        recorder = GameRecorder()
        recorder.start_game(2, ["Alice", "Bob"], 5, None)
        recorder.record_round_start(1)
        recorder.record_roll(1, 1, (3, 4), 0, 7)

        data = recorder.to_dict()
        assert "events" in data
        assert "metadata" in data
        assert len(data["events"]) == 3
        assert data["metadata"]["num_players"] == 2

    def test_clear(self) -> None:
        """Test clearing recorder state."""
        recorder = GameRecorder()
        recorder.start_game(2, ["Alice", "Bob"], 5, None)
        recorder.record_round_start(1)

        assert len(recorder.events) > 0
        assert len(recorder.metadata) > 0

        recorder.clear()

        assert recorder.events == []
        assert recorder.metadata == {}

    def test_complete_game_sequence(self) -> None:
        """Test recording a complete game sequence."""
        recorder = GameRecorder()

        # Game start
        recorder.start_game(2, ["Alice", "Bob"], 1, 42)

        # Round 1
        recorder.record_round_start(1)
        recorder.record_roll(1, 1, (3, 4), 0, 7)
        recorder.record_roll(1, 2, (2, 6), 7, 15)
        recorder.record_bank(1, 0, "Alice", 15, 0, 15)
        recorder.record_bank(1, 1, "Bob", 15, 0, 15)
        recorder.record_round_end(1, "all_banked", 15, {0: 15, 1: 15})

        # Game end
        recorder.record_game_end({0: 15, 1: 15}, [0, 1], ["Alice", "Bob"])

        # 8 events total: game_start, round_start, 2 rolls, 2 banks, round_end, game_end
        assert len(recorder.events) == 8
        assert recorder.events[0]["type"] == "game_start"
        assert recorder.events[-1]["type"] == "game_end"


class TestSaveLoadReplay:
    """Tests for save_replay and load_replay functions."""

    def test_save_and_load_replay(self) -> None:
        """Test saving and loading a replay."""
        recorder = GameRecorder()
        recorder.start_game(2, ["Alice", "Bob"], 5, 42)
        recorder.record_round_start(1)
        recorder.record_roll(1, 1, (3, 4), 0, 7)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            save_replay(recorder, temp_path)

            # Load it back
            loaded_data = load_replay(temp_path)

            # Verify data
            assert "events" in loaded_data
            assert "metadata" in loaded_data
            assert len(loaded_data["events"]) == 3
            assert loaded_data["metadata"]["num_players"] == 2
            assert loaded_data["events"][0]["type"] == "game_start"

        finally:
            # Clean up
            Path(temp_path).unlink()

    def test_save_creates_directory(self) -> None:
        """Test that save_replay creates parent directories if needed."""
        recorder = GameRecorder()
        recorder.start_game(2, ["Alice", "Bob"], 5, None)

        temp_dir = Path(tempfile.gettempdir()) / "bank_test_replays" / "subdir"
        temp_file = temp_dir / "test.json"

        try:
            save_replay(recorder, str(temp_file))
            assert temp_file.exists()

            loaded_data = load_replay(str(temp_file))
            assert loaded_data["metadata"]["num_players"] == 2

        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()
            if temp_dir.parent.exists():
                temp_dir.parent.rmdir()

    def test_load_nonexistent_file(self) -> None:
        """Test loading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_replay("/path/that/does/not/exist.json")

    def test_round_trip_preserves_data(self) -> None:
        """Test that save and load preserves all data (with JSON int key conversion)."""
        recorder = GameRecorder()

        # Record a full game
        recorder.start_game(4, ["Alice", "Bob", "Charlie", "Diana"], 2, 123)
        recorder.record_round_start(1)
        recorder.record_roll(1, 1, (6, 6), 0, 12)
        recorder.record_bank(1, 0, "Alice", 12, 0, 12)
        recorder.record_round_end(1, "all_banked", 0, {0: 12, 1: 0, 2: 0, 3: 0})
        recorder.record_game_end({0: 12, 1: 0, 2: 0, 3: 0}, [0], ["Alice"])

        # Save and load
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            save_replay(recorder, temp_path)
            loaded_data = load_replay(temp_path)

            # Check structure
            assert len(loaded_data["events"]) == 6
            assert loaded_data["metadata"]["num_players"] == 4
            assert loaded_data["metadata"] == recorder.metadata

            # Check event types are preserved
            event_types = [e["type"] for e in loaded_data["events"]]
            assert event_types == ["game_start", "round_start", "roll", "bank", "round_end", "game_end"]

            # Note: JSON converts dict int keys to strings, so we don't do exact equality
            # but verify the data structure is correct
            assert "data" in loaded_data["events"][0]
            assert "timestamp" in loaded_data["events"][0]

        finally:
            Path(temp_path).unlink()
