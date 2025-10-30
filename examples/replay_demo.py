"""Demonstration of BANK! game replay recording and viewing.

This example shows how to:
1. Record a game using GameRecorder
2. Save the replay to a JSON file
3. Load and view replays with ReplayViewer
4. Analyze specific rounds and player statistics

Run with: python examples/replay_demo.py
"""

import random
import tempfile
from pathlib import Path

from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import AggressiveAgent, ConservativeAgent, SmartAgent
from bank.game.engine import BankGame
from bank.replay.recorder import GameRecorder, load_replay, save_replay
from bank.replay.viewer import ReplayViewer


def record_game() -> str:
    """Record a game and save it to a temporary file.

    Returns:
        Path to the saved replay file

    """
    print("=" * 60)
    print("RECORDING A GAME")
    print("=" * 60)

    # Create recorder
    recorder = GameRecorder()

    # Set up agents
    agents = [
        SmartAgent(player_id=0, name="Alice (Smart)"),
        AggressiveAgent(player_id=1, name="Bob (Aggressive)"),
        ConservativeAgent(player_id=2, name="Charlie (Conservative)"),
        RandomAgent(player_id=3, name="Diana (Random)"),
    ]

    # Create game with recorder
    game = BankGame(
        num_players=4,
        player_names=["Alice (Smart)", "Bob (Aggressive)", "Charlie (Conservative)", "Diana (Random)"],
        total_rounds=5,
        agents=agents,
        recorder=recorder,  # Attach the recorder
        rng=random.Random(42),  # Use seed for reproducible demo
    )

    # Play the game
    print("\nPlaying game with 4 agents...")
    print("- Alice uses SmartAgent strategy")
    print("- Bob uses AggressiveAgent strategy")
    print("- Charlie uses ConservativeAgent strategy")
    print("- Diana uses RandomAgent strategy")
    print()

    game.play_game()

    # Save replay to temporary file
    temp_dir = Path(tempfile.gettempdir()) / "bank_replays"
    temp_dir.mkdir(exist_ok=True)
    replay_path = str(temp_dir / "demo_game.json")

    save_replay(recorder, replay_path)
    print(f"\n✓ Game recorded and saved to: {replay_path}\n")

    return replay_path


def view_replay(replay_path: str) -> None:
    """Load and display a replay using various viewer methods.

    Args:
        replay_path: Path to the replay file

    """
    print("=" * 60)
    print("VIEWING REPLAY")
    print("=" * 60)

    # Load the replay
    replay_data = load_replay(replay_path)
    viewer = ReplayViewer(replay_data)

    # Display summary
    print("\n--- GAME SUMMARY ---")
    viewer.print_summary()

    # Display play-by-play
    print("\n" + "=" * 60)
    print("--- PLAY-BY-PLAY NARRATIVE ---")
    print("=" * 60)
    viewer.print_play_by_play()

    # Analyze specific rounds
    print("\n" + "=" * 60)
    print("--- ROUND ANALYSIS ---")
    print("=" * 60)

    # Analyze round 3 (middle of the game)
    print("\nDetailed analysis of Round 3:")
    viewer.analyze_round(3)

    # Display player statistics
    print("\n" + "=" * 60)
    print("--- PLAYER STATISTICS ---")
    print("=" * 60)

    # Get player stats for each player
    for player_id in range(4):
        print(f"\nPlayer {player_id} statistics:")
        viewer.print_player_stats(player_id)


def demonstrate_replay_analysis() -> None:
    """Run a complete demonstration of replay recording and viewing."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "BANK! REPLAY DEMO" + " " * 26 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("This demo shows how to record and analyze BANK! games.")
    print()

    # Record a game
    replay_path = record_game()

    # View the replay
    view_replay(replay_path)

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey takeaways:")
    print("• GameRecorder captures all game events automatically")
    print("• Replays are saved as human-readable JSON files")
    print("• ReplayViewer provides multiple analysis perspectives:")
    print("  - Summary: Overview with final scores and event counts")
    print("  - Play-by-play: Complete game narrative with emojis")
    print("  - Round analysis: Detailed breakdown of specific rounds")
    print("  - Player stats: Banking patterns and decision metrics")
    print()
    print("Try modifying this script to:")
    print("• Record games with different agent combinations")
    print("• Analyze different rounds")
    print("• Compare player statistics across multiple replays")
    print()


if __name__ == "__main__":
    demonstrate_replay_analysis()
