"""Game State Inspection Example.

This example shows how to inspect and analyze game state during a BANK! dice game.
Demonstrates programmatic game execution, state access, and statistical analysis.
"""

from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import SmartAgent, ThresholdAgent
from bank.game.engine import BankGame


def analyze_game_state(game: BankGame) -> None:
    """Print detailed analysis of current game state.

    Args:
        game: The game instance to analyze

    """
    state = game.state

    print("\n" + "=" * 60)
    print("Game State Analysis")
    print("=" * 60)

    # Overall game info
    print(
        f"\nGame Progress: Round {state.current_round.round_number if state.current_round else 0}/{state.total_rounds}"
    )
    print(f"Game Over: {state.game_over}")

    # Current round info
    if state.current_round:
        round_state = state.current_round
        print("\nCurrent Round:")
        print(f"  Roll Count: {round_state.roll_count}")
        print(f"  Bank Value: {round_state.current_bank} points")
        print(f"  Active Players: {len(round_state.active_player_ids)}/{state.num_players}")

        if round_state.last_roll:
            die1, die2 = round_state.last_roll
            print(f"  Last Roll: [{die1}] [{die2}] = {die1 + die2}")

            # Analyze roll significance
            if die1 + die2 == 7:  # noqa: PLR2004
                if round_state.roll_count <= 3:  # noqa: PLR2004
                    print("    → SEVEN! Added 70 points")
                else:
                    print("    → SEVEN! Round ends")
            elif die1 == die2:
                if round_state.roll_count <= 3:  # noqa: PLR2004
                    print(f"    → DOUBLES! Added {die1 + die2} points")
                else:
                    print("    → DOUBLES! Bank doubled")

    # Player details
    print("\nPlayer Details:")
    sorted_players = sorted(state.players, key=lambda p: p.score, reverse=True)

    for rank, player in enumerate(sorted_players, 1):
        print(f"\n  {rank}. {player.name}:")
        print(f"     Score: {player.score} points")
        print(f"     Banked this round: {'Yes' if player.has_banked_this_round else 'No'}")

        if state.current_round:
            is_active = player.player_id in state.current_round.active_player_ids
            print(f"     Status: {'⚡ Active' if is_active else '💤 Out'}")

    # Calculate statistics
    if state.players:
        avg_score = sum(p.score for p in state.players) / len(state.players)
        max_score = max(p.score for p in state.players)
        min_score = min(p.score for p in state.players)
        print("\nScore Statistics:")
        print(f"  Average: {avg_score:.1f} points")
        print(f"  Highest: {max_score} points")
        print(f"  Lowest: {min_score} points")
        print(f"  Spread: {max_score - min_score} points")


def play_with_inspection(num_rounds: int = 3) -> None:
    """Play a game with periodic state inspection.

    Args:
        num_rounds: Number of rounds to play

    """
    print("=" * 60)
    print("Game State Inspection Example")
    print("=" * 60)

    # Create game with 3 players
    player_names = ["Alice", "Bob", "Charlie"]
    game = BankGame(
        num_players=3,
        player_names=player_names,
        total_rounds=num_rounds,
        rng=None,
    )

    # Create agents with different strategies
    agents = [
        RandomAgent(player_id=0, name="Alice", seed=42),
        ThresholdAgent(player_id=1, name="Bob", threshold=60),
        SmartAgent(player_id=2, name="Charlie"),
    ]

    game.agents = agents

    print(f"\nPlaying {num_rounds}-round game with inspection after each round...")

    # Play round by round with analysis
    for round_num in range(1, num_rounds + 1):
        print(f"\n{'=' * 60}")
        print(f"STARTING ROUND {round_num}")
        print(f"{'=' * 60}")

        # Play one round
        game.start_new_round()
        game.play_round()

        # Analyze state after round
        analyze_game_state(game)

        # Check if game ended early
        if game.state.game_over:
            print("\n⚠️  Game ended early!")
            break

    # Final analysis
    print("\n" + "=" * 60)
    print("FINAL GAME STATE")
    print("=" * 60)
    analyze_game_state(game)

    # Determine winner
    if game.state.game_over:
        max_score = max(p.score for p in game.state.players)
        winners = [p for p in game.state.players if p.score == max_score]

        if len(winners) == 1:
            print(f"\n🏆 Winner: {winners[0].name} with {winners[0].score} points!")
        else:
            winner_names = ", ".join(w.name for w in winners)
            print(f"\n🤝 Tie between: {winner_names} with {max_score} points each!")


def inspect_single_round() -> None:
    """Demonstrate detailed inspection of a single round.

    This shows how to access all the information available during a round.
    """
    print("\n" + "=" * 60)
    print("Single Round Deep Inspection")
    print("=" * 60)

    game = BankGame(num_players=2, player_names=["Player 1", "Player 2"], total_rounds=1)

    # Create simple agents
    agents = [
        ThresholdAgent(player_id=0, name="Player 1", threshold=50),
        ThresholdAgent(player_id=1, name="Player 2", threshold=80),
    ]
    game.agents = agents

    # Start a round
    game.start_new_round()

    print("\nInspecting round structure...")
    print(f"Round number: {game.state.current_round.round_number}")
    print(f"Initial bank: {game.state.current_round.current_bank}")
    print(f"Initial active players: {game.state.current_round.active_player_ids}")
    print(f"Roll count: {game.state.current_round.roll_count}")

    # Simulate a few rolls manually to show inspection
    for i in range(3):
        print(f"\n--- Roll {i + 1} ---")
        game.roll_dice()

        if game.state.current_round.last_roll:
            die1, die2 = game.state.current_round.last_roll
            print(f"Dice: [{die1}] [{die2}]")
            print(f"Bank now: {game.state.current_round.current_bank}")
            print(f"Active players: {len(game.state.current_round.active_player_ids)}")

        # Poll for decisions
        banked = game.poll_decisions()
        if banked:
            print(f"Players who banked: {banked}")

        if game.is_round_over():
            print("Round ended!")
            break

    print("\n" + "=" * 60)


def main() -> None:
    """Run all inspection examples."""
    # Example 1: Play full game with periodic inspection
    play_with_inspection(num_rounds=3)

    # Example 2: Deep dive into single round
    inspect_single_round()

    print("\n" + "=" * 60)
    print("Inspection complete!")
    print("=" * 60)
    print("\nKey Inspection Points:")
    print("  - GameState: Overall game info (players, rounds, game_over)")
    print("  - RoundState: Current round info (rolls, bank, active players)")
    print("  - PlayerState: Individual player data (score, has_banked)")
    print("  - Use analyze_game_state() as template for custom analysis")
    print()


if __name__ == "__main__":
    main()
