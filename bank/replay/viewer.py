"""Replay viewing and analysis tools.

Provides utilities for viewing and analyzing recorded games.
"""

from typing import Any


class ReplayViewer:
    """Views and analyzes recorded games.

    Loads replay data and provides methods to display game progression
    step-by-step or analyze specific aspects of the game.
    """

    def __init__(self, replay_data: dict[str, Any]) -> None:
        """Initialize viewer with replay data.

        Args:
            replay_data: Replay data from load_replay()

        """
        self.metadata = replay_data.get("metadata", {})
        self.events = replay_data.get("events", [])
        self.current_index = 0

    def print_summary(self) -> None:
        """Print a summary of the game."""
        print("=" * 70)
        print("GAME REPLAY SUMMARY")
        print("=" * 70)

        # Game metadata
        print(f"\nPlayers: {self.metadata.get('num_players')}")
        player_names = self.metadata.get("player_names", [])
        for i, name in enumerate(player_names):
            print(f"  {i}. {name}")

        print(f"\nTotal Rounds: {self.metadata.get('total_rounds')}")
        if self.metadata.get("seed") is not None:
            print(f"Seed: {self.metadata.get('seed')}")

        # Find game end event
        game_end = next(
            (e for e in self.events if e["type"] == "game_end"),
            None,
        )

        if game_end:
            data = game_end["data"]
            print("\nFinal Scores:")
            final_scores = data.get("final_scores", {})
            sorted_scores = sorted(
                final_scores.items(),
                key=lambda x: x[1],
                reverse=True,
            )
            for player_id, score in sorted_scores:
                name = player_names[int(player_id)] if int(player_id) < len(player_names) else f"Player {player_id}"
                is_winner = int(player_id) in data.get("winner_ids", [])
                marker = "🏆" if is_winner else "  "
                print(f"  {marker} {name}: {score} points")

            duration = data.get("duration_seconds", 0)
            print(f"\nGame Duration: {duration:.1f} seconds")

        # Event statistics
        event_counts = {}
        for event in self.events:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        print("\nEvent Counts:")
        for event_type, count in sorted(event_counts.items()):
            print(f"  {event_type}: {count}")

        print()

    def print_play_by_play(self) -> None:
        """Print a play-by-play of the entire game."""
        print("\n" + "=" * 70)
        print("PLAY-BY-PLAY")
        print("=" * 70 + "\n")

        player_names = self.metadata.get("player_names", [])

        for event in self.events:
            event_type = event["type"]
            data = event["data"]

            if event_type == "game_start":
                print("🎮 GAME START")
                print(f"   Players: {', '.join(player_names)}")
                print(f"   Rounds: {data.get('total_rounds')}\n")

            elif event_type == "round_start":
                round_num = data.get("round_number")
                print(f"\n📍 ROUND {round_num} START")
                print("-" * 70)

            elif event_type == "roll":
                roll_count = data.get("roll_count")
                dice = data.get("dice", [])
                bank_after = data.get("bank_after")
                delta = data.get("delta")

                dice_str = f"[{dice[0]}] [{dice[1]}]" if len(dice) == 2 else str(dice)
                print(f"   Roll #{roll_count}: {dice_str} → Bank: {bank_after} ({delta:+d})")

            elif event_type == "bank":
                player_id = data.get("player_id")
                player_name = data.get("player_name")
                amount = data.get("amount")
                score_after = data.get("score_after")
                print(f"   💰 {player_name} BANKS {amount} points! (Total: {score_after})")

            elif event_type == "round_end":
                reason = data.get("reason")
                final_bank = data.get("final_bank")

                if reason == "seven_rolled":
                    print(f"   ❌ ROUND OVER - Seven rolled! Bank lost ({final_bank} points)")
                elif reason == "all_banked":
                    print("   ✅ ROUND OVER - All players banked")

                player_scores = data.get("player_scores", {})
                print(
                    f"   Scores: {', '.join(f'{player_names[int(pid)]}: {score}' for pid, score in sorted(player_scores.items()))}"
                )

            elif event_type == "game_end":
                print("\n" + "=" * 70)
                print("🏁 GAME OVER")
                print("=" * 70)
                winner_names = data.get("winner_names", [])
                if len(winner_names) == 1:
                    print(f"   🏆 Winner: {winner_names[0]}")
                else:
                    print(f"   🤝 Tie: {', '.join(winner_names)}")

                final_scores = data.get("final_scores", {})
                print("\n   Final Standings:")
                sorted_scores = sorted(
                    final_scores.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
                for rank, (player_id, score) in enumerate(sorted_scores, 1):
                    name = player_names[int(player_id)] if int(player_id) < len(player_names) else f"Player {player_id}"
                    print(f"     {rank}. {name}: {score} points")

        print()

    def analyze_round(self, round_number: int) -> None:
        """Analyze a specific round in detail.

        Args:
            round_number: Round number to analyze

        """
        print(f"\n{'=' * 70}")
        print(f"ROUND {round_number} ANALYSIS")
        print("=" * 70 + "\n")

        round_events = [e for e in self.events if e.get("data", {}).get("round_number") == round_number]

        if not round_events:
            print(f"No events found for round {round_number}")
            return

        rolls = [e for e in round_events if e["type"] == "roll"]
        banks = [e for e in round_events if e["type"] == "bank"]
        round_end = next((e for e in round_events if e["type"] == "round_end"), None)

        print(f"Total Rolls: {len(rolls)}")
        print(f"Players Banked: {len(banks)}")

        if rolls:
            print("\nRoll Details:")
            for i, roll in enumerate(rolls, 1):
                data = roll["data"]
                dice = data.get("dice", [])
                bank_after = data.get("bank_after")
                delta = data.get("delta")
                dice_str = f"[{dice[0]}] [{dice[1]}]" if len(dice) == 2 else str(dice)
                print(f"  Roll {i}: {dice_str} → +{delta} (Bank: {bank_after})")

        if banks:
            print("\nBanking Order:")
            for i, bank in enumerate(banks, 1):
                data = bank["data"]
                player_name = data.get("player_name")
                amount = data.get("amount")
                print(f"  {i}. {player_name} banked {amount} points")

        if round_end:
            data = round_end["data"]
            reason = data.get("reason")
            print(f"\nRound End: {reason}")
            print(f"Final Bank: {data.get('final_bank')}")

        print()

    def get_player_stats(self, player_id: int) -> dict[str, Any]:
        """Get statistics for a specific player.

        Args:
            player_id: Player ID to analyze

        Returns:
            Dictionary of player statistics

        """
        player_names = self.metadata.get("player_names", [])
        player_name = player_names[player_id] if player_id < len(player_names) else f"Player {player_id}"

        bank_events = [e for e in self.events if e["type"] == "bank" and e["data"].get("player_id") == player_id]

        total_banked = sum(e["data"].get("amount", 0) for e in bank_events)
        num_banks = len(bank_events)
        avg_bank = total_banked / num_banks if num_banks > 0 else 0

        # Find final score
        game_end = next((e for e in self.events if e["type"] == "game_end"), None)
        final_score = 0
        if game_end:
            final_scores = game_end["data"].get("final_scores", {})
            final_score = final_scores.get(str(player_id), 0)

        return {
            "name": player_name,
            "final_score": final_score,
            "times_banked": num_banks,
            "total_banked": total_banked,
            "average_bank": avg_bank,
        }

    def print_player_stats(self, player_id: int) -> None:
        """Print statistics for a specific player.

        Args:
            player_id: Player ID to analyze

        """
        stats = self.get_player_stats(player_id)

        print(f"\n{'=' * 70}")
        print(f"PLAYER STATS: {stats['name']}")
        print("=" * 70)
        print(f"\nFinal Score: {stats['final_score']}")
        print(f"Times Banked: {stats['times_banked']}")
        print(f"Total Banked: {stats['total_banked']}")
        print(f"Average Bank: {stats['average_bank']:.1f}")
        print()
