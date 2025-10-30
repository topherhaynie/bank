"""Programmatic Tournament Example.

This example shows how to run multiple games programmatically and collect statistics.
Demonstrates how to create agents, run games in batch, and analyze performance.
"""

from collections import defaultdict

from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import (
    AdaptiveAgent,
    AggressiveAgent,
    ConservativeAgent,
    SmartAgent,
    ThresholdAgent,
)
from bank.game.engine import BankGame


def run_tournament(agent_configs: list[dict], num_games: int = 50, num_rounds: int = 5) -> dict:
    """Run a tournament between multiple agents.

    Args:
        agent_configs: List of dicts with 'class', 'name', and optional 'kwargs'
        num_games: Number of games to play
        num_rounds: Number of rounds per game

    Returns:
        Dictionary of statistics per agent

    """
    stats = defaultdict(
        lambda: {
            "wins": 0,
            "total_score": 0,
            "games": 0,
            "avg_rounds_to_bank": 0.0,
            "total_banks": 0,
        }
    )

    print(f"\n{'=' * 70}")
    print(f"Running Tournament: {num_games} games, {num_rounds} rounds each")
    print(f"{'=' * 70}\n")
    print(f"Competitors: {', '.join(cfg['name'] for cfg in agent_configs)}")
    print()

    for game_num in range(num_games):
        if (game_num + 1) % 10 == 0:  # Progress update every 10 games
            print(f"  Progress: {game_num + 1}/{num_games} games completed...")

        # Create game
        player_names = [cfg["name"] for cfg in agent_configs]
        game = BankGame(
            num_players=len(agent_configs),
            player_names=player_names,
            total_rounds=num_rounds,
        )

        # Create agent instances
        agents = []
        for i, cfg in enumerate(agent_configs):
            agent_class = cfg["class"]
            kwargs = cfg.get("kwargs", {})
            agent = agent_class(player_id=i, name=cfg["name"], **kwargs)
            agents.append(agent)

        # Set agents and run game
        game.agents = agents
        game.play_game()

        # Collect statistics
        max_score = max(p.score for p in game.state.players)
        for player in game.state.players:
            agent_name = player.name
            stats[agent_name]["games"] += 1
            stats[agent_name]["total_score"] += player.score

            # Check if winner (handle ties)
            if player.score == max_score:
                stats[agent_name]["wins"] += 1

    return stats


def print_tournament_results(stats: dict) -> None:
    """Print formatted tournament results.

    Args:
        stats: Statistics dictionary from run_tournament

    """
    print(f"\n{'=' * 70}")
    print("Tournament Results")
    print(f"{'=' * 70}\n")

    # Sort by wins, then by total score
    sorted_agents = sorted(
        stats.items(),
        key=lambda x: (x[1]["wins"], x[1]["total_score"]),
        reverse=True,
    )

    # Print header
    print(f"{'Rank':<6} {'Agent':<20} {'Wins':<8} {'Avg Score':<12} {'Win Rate':<10}")
    print("-" * 70)

    # Print each agent's stats
    for rank, (agent_name, agent_stats) in enumerate(sorted_agents, 1):
        wins = agent_stats["wins"]
        games = agent_stats["games"]
        avg_score = agent_stats["total_score"] / games if games > 0 else 0
        win_rate = (wins / games * 100) if games > 0 else 0

        # Add medal for top 3
        medal = ""
        if rank == 1:
            medal = "🥇"
        elif rank == 2:  # noqa: PLR2004
            medal = "🥈"
        elif rank == 3:  # noqa: PLR2004
            medal = "🥉"

        print(f"{rank:<6} {agent_name:<20} {wins:<8} {avg_score:<12.1f} {win_rate:<9.1f}% {medal}")

    print()


def compare_strategies() -> None:
    """Compare different banking strategies in a tournament."""
    print("=" * 70)
    print("Strategy Comparison Tournament")
    print("=" * 70)

    # Define agents to compete
    agent_configs = [
        {"class": RandomAgent, "name": "Random", "kwargs": {"seed": 42}},
        {"class": ThresholdAgent, "name": "Threshold50", "kwargs": {"threshold": 50}},
        {"class": ThresholdAgent, "name": "Threshold80", "kwargs": {"threshold": 80}},
        {"class": ConservativeAgent, "name": "Conservative"},
        {"class": AggressiveAgent, "name": "Aggressive"},
        {"class": SmartAgent, "name": "Smart"},
        {"class": AdaptiveAgent, "name": "Adaptive"},
    ]

    # Run tournament
    stats = run_tournament(agent_configs, num_games=100, num_rounds=5)

    # Display results
    print_tournament_results(stats)

    # Additional analysis
    print("=" * 70)
    print("Strategy Analysis")
    print("=" * 70)
    print("\nKey Insights:")
    print("  • Conservative: Banks early, minimizes risk")
    print("  • Aggressive: Takes more chances, pursues high scores")
    print("  • Smart: Considers game state and position")
    print("  • Adaptive: Adjusts strategy based on round progress")
    print("  • Threshold: Fixed banking point (50 or 80)")
    print("  • Random: Baseline for comparison")
    print()


def quick_comparison() -> None:
    """Quick 2-player comparison for testing strategies."""
    print("\n" + "=" * 70)
    print("Quick Head-to-Head: Smart vs Adaptive")
    print("=" * 70)

    agent_configs = [
        {"class": SmartAgent, "name": "Smart"},
        {"class": AdaptiveAgent, "name": "Adaptive"},
    ]

    stats = run_tournament(agent_configs, num_games=20, num_rounds=3)
    print_tournament_results(stats)


def main() -> None:
    """Run tournament examples."""
    # Example 1: Quick head-to-head
    quick_comparison()

    # Example 2: Full strategy comparison
    compare_strategies()


if __name__ == "__main__":
    main()
