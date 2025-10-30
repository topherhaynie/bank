"""Game recording and replay functionality.

Records game events during play for later analysis and replay.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class GameRecorder:
    """Records game events for replay and analysis.

    Captures all significant game events (rolls, banks, round progression)
    with timestamps for complete game reconstruction.
    """

    def __init__(self) -> None:
        """Initialize a new game recorder."""
        self.events: list[dict[str, Any]] = []
        self.metadata: dict[str, Any] = {}
        self.start_time: datetime | None = None

    def start_game(
        self,
        num_players: int,
        player_names: list[str],
        total_rounds: int,
        seed: int | None = None,
    ) -> None:
        """Record game start.

        Args:
            num_players: Number of players in the game
            player_names: Names of all players
            total_rounds: Total number of rounds
            seed: Random seed if used

        """
        self.start_time = datetime.now()
        self.metadata = {
            "num_players": num_players,
            "player_names": player_names,
            "total_rounds": total_rounds,
            "seed": seed,
            "start_time": self.start_time.isoformat(),
        }
        self._add_event("game_start", self.metadata.copy())

    def record_round_start(self, round_number: int) -> None:
        """Record the start of a round.

        Args:
            round_number: Round number (1-based)

        """
        self._add_event("round_start", {"round_number": round_number})

    def record_roll(
        self,
        round_number: int,
        roll_count: int,
        dice: tuple[int, int],
        bank_before: int,
        bank_after: int,
    ) -> None:
        """Record a dice roll.

        Args:
            round_number: Current round number
            roll_count: Number of rolls this round
            dice: The two dice values
            bank_before: Bank value before roll
            bank_after: Bank value after roll

        """
        self._add_event(
            "roll",
            {
                "round_number": round_number,
                "roll_count": roll_count,
                "dice": list(dice),
                "bank_before": bank_before,
                "bank_after": bank_after,
                "delta": bank_after - bank_before,
            },
        )

    def record_bank(
        self,
        round_number: int,
        player_id: int,
        player_name: str,
        amount: int,
        score_before: int,
        score_after: int,
    ) -> None:
        """Record a player banking.

        Args:
            round_number: Current round number
            player_id: ID of player who banked
            player_name: Name of player who banked
            amount: Amount banked
            score_before: Player's score before banking
            score_after: Player's score after banking

        """
        self._add_event(
            "bank",
            {
                "round_number": round_number,
                "player_id": player_id,
                "player_name": player_name,
                "amount": amount,
                "score_before": score_before,
                "score_after": score_after,
            },
        )

    def record_round_end(
        self,
        round_number: int,
        reason: str,
        final_bank: int,
        player_scores: dict[int, int],
    ) -> None:
        """Record the end of a round.

        Args:
            round_number: Round number that ended
            reason: Reason for round end ("all_banked", "seven_rolled")
            final_bank: Final bank value (0 if lost)
            player_scores: Current scores of all players

        """
        self._add_event(
            "round_end",
            {
                "round_number": round_number,
                "reason": reason,
                "final_bank": final_bank,
                "player_scores": player_scores.copy(),
            },
        )

    def record_game_end(
        self,
        final_scores: dict[int, int],
        winner_ids: list[int],
        winner_names: list[str],
    ) -> None:
        """Record game end.

        Args:
            final_scores: Final scores of all players
            winner_ids: IDs of winning player(s)
            winner_names: Names of winning player(s)

        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() if self.start_time else 0

        self._add_event(
            "game_end",
            {
                "final_scores": final_scores.copy(),
                "winner_ids": winner_ids,
                "winner_names": winner_names,
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
            },
        )

    def _add_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Add an event to the recording.

        Args:
            event_type: Type of event
            data: Event data

        """
        timestamp = datetime.now()
        event = {
            "type": event_type,
            "timestamp": timestamp.isoformat(),
            "data": data,
        }
        self.events.append(event)

    def to_dict(self) -> dict[str, Any]:
        """Export recording to a dictionary.

        Returns:
            Dictionary representation of the recording

        """
        return {
            "metadata": self.metadata,
            "events": self.events,
        }

    def clear(self) -> None:
        """Clear all recorded events."""
        self.events.clear()
        self.metadata.clear()
        self.start_time = None


def save_replay(recorder: GameRecorder, filepath: str | Path) -> None:
    """Save a game recording to a file.

    Args:
        recorder: GameRecorder instance with recorded game
        filepath: Path to save the replay file (JSON format)

    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    data = recorder.to_dict()
    with filepath.open("w") as f:
        json.dump(data, f, indent=2)


def load_replay(filepath: str | Path) -> dict[str, Any]:
    """Load a game recording from a file.

    Args:
        filepath: Path to the replay file

    Returns:
        Dictionary containing metadata and events

    """
    filepath = Path(filepath)
    with filepath.open() as f:
        return json.load(f)
