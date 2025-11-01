"""Programmatic Tournament Example.

This example shows how to run multiple games programmatically and collect statistics.
Demonstrates how to create agents, run games in batch, and analyze performance.
"""

import argparse
from collections import defaultdict

from tqdm import tqdm

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
            "wins": 0,  # solo wins only
            "tie_wins": 0,  # games where agent tied for first
            "weighted_wins": 0.0,  # fractional win for ties
            "total_score": 0,
            "games": 0,
            "avg_rounds_to_bank": 0.0,
            "total_banks": 0,
        },
    )
    # Head-to-head: stats[agent]['h2h'][opponent] = [games_played, games_won]
    for cfg in agent_configs:
        stats[cfg["name"]]["h2h"] = defaultdict(lambda: [0, 0])

    print(f"\n{'=' * 70}")
    print(f"Running Tournament: {num_games} games, {num_rounds} rounds each")
    print(f"{'=' * 70}\n")
    print(f"Competitors: {', '.join(cfg['name'] for cfg in agent_configs)}")
    print()

    leader = None
    leader_wins = 0
    tie_games = 0
    with tqdm(total=num_games, desc="Tournament Progress", ncols=100) as pbar:
        for game_num in range(num_games):
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
            winners = [player for player in game.state.players if player.score == max_score]
            if len(winners) > 1:
                tie_games += 1
            # Head-to-head: for each pair, track who scored higher
            player_scores = {p.name: p.score for p in game.state.players}
            for agent_name in player_scores:
                for opponent_name in player_scores:
                    if agent_name == opponent_name:
                        continue
                    stats[agent_name]["h2h"][opponent_name][0] += 1
                    if player_scores[agent_name] > player_scores[opponent_name]:
                        stats[agent_name]["h2h"][opponent_name][1] += 1

            for player in game.state.players:
                agent_name = player.name
                stats[agent_name]["games"] += 1
                stats[agent_name]["total_score"] += player.score
                # Check if winner (handle ties)
                if player.score == max_score:
                    if len(winners) == 1:
                        stats[agent_name]["wins"] += 1  # solo win
                        stats[agent_name]["weighted_wins"] += 1.0
                    else:
                        stats[agent_name]["tie_wins"] += 1  # tied for first
                        stats[agent_name]["weighted_wins"] += 1.0 / len(winners)

            # Update leader info
            leader, leader_wins = max(stats.items(), key=lambda x: x[1]["wins"])
            pbar.set_postfix({"leader": leader, "wins": leader_wins["wins"]})
            pbar.update(1)
    stats["_tie_games"] = tie_games
    stats["_num_games"] = num_games
    return stats


def print_tournament_results(stats: dict) -> None:
    # Head-to-head matrix output
    agent_names = [k for k, v in stats.items() if isinstance(v, dict) and "h2h" in v]
    agent_names.sort()
    for row_agent in agent_names:
        row = f"{row_agent[:14]:>16}"
        for col_agent in agent_names:
            if row_agent == col_agent:
                row += f"{'--':>13}"
            else:
                games, wins = stats[row_agent]["h2h"][col_agent]
                pct = (wins / games * 100) if games > 0 else 0.0
                row += f"{pct:>12.1f}% "
    """Print formatted tournament results with proper standard competition ranking and tie counts."""
    print(f"\n{'=' * 70}")
    print("Tournament Results")
    print(f"{'=' * 70}\n")

    # Filter out debug keys (like '_tie_games', '_num_games')
    agent_items = [(k, v) for k, v in stats.items() if isinstance(v, dict) and "h2h" in v]
    agent_names = [k for k, _ in agent_items]
    # Compute losses and average score for each agent
    for agent_name, agent_stats in agent_items:
        games = agent_stats["games"]
        wins = agent_stats["wins"]
        tie_wins = agent_stats.get("tie_wins", 0)
        agent_stats["losses"] = games - wins - tie_wins
        agent_stats["avg_score"] = agent_stats["total_score"] / games if games > 0 else 0
    # Sort by fewest losses (ascending), then most solo wins (descending), then weighted wins (descending), then avg score (descending)
    sorted_agents = sorted(
        agent_items,
        key=lambda x: (
            x[1]["losses"],
            -x[1]["wins"],
            -x[1].get("weighted_wins", 0),
            -x[1]["avg_score"],
        ),
    )

    # Group by wins for standard competition ranking
    results = []
    rank = 1
    i = 0
    while i < len(sorted_agents):
        win_group = []
        wins = sorted_agents[i][1]["wins"]
        # Collect all agents with this win count
        while i < len(sorted_agents) and sorted_agents[i][1]["wins"] == wins:
            win_group.append(sorted_agents[i])
            i += 1
        results.append((rank, win_group))
        rank += len(win_group)

    # Print header
    print(
        f"{'Rank':<5} {'Agent':<22} {'Losses':<8} {'Wins':<6} {'Ties':<6} {'WtdWins':<8} {'Avg Score':<10} {'Win Rate':<13} {'Tie Rate':<10} {'Medal':<5}",
    )
    print("-" * 110)

    # Print each group of tied agents
    for rank, win_group in results:
        for idx, (agent_name, agent_stats) in enumerate(win_group):
            if agent_name.startswith("_"):
                continue  # skip debug keys
            wins = agent_stats["wins"]
            tie_wins = agent_stats.get("tie_wins", 0)
            weighted_wins = agent_stats.get("weighted_wins", 0.0)
            losses = agent_stats.get("losses", 0)
            games = agent_stats["games"]
            avg_score = agent_stats["avg_score"]
            win_rate = (wins / games * 100) if games > 0 else 0
            tie_rate = (tie_wins / games * 100) if games > 0 else 0
            weighted_win_rate = (weighted_wins / games * 100) if games > 0 else 0
            medal = ""
            if rank == 1:
                medal = "🥇"
            elif rank == 2:
                medal = "🥈"
            elif rank == 3:
                medal = "🥉"
            rank_str = str(rank) if idx == 0 else ""
            medal_str = medal if idx == 0 else ""
            weighted_win_str = f"{weighted_wins:.2f} ({weighted_win_rate:.1f}%)"
            win_rate_str = f"{wins} ({win_rate:.1f}%)"
            tie_rate_str = f"{tie_wins} ({tie_rate:.1f}%)"
            print(
                f"{rank_str:<5} {agent_name:<22} {losses:<8} {wins:<6} {tie_wins:<6} {weighted_win_str:<8} {avg_score:<10.1f} {win_rate_str:<13} {tie_rate_str:<10} {medal_str:<5}",
            )
    print()


def compare_strategies(num_games=1000, num_rounds=20) -> None:
    """Compare different banking strategies in a tournament."""
    # Define agents to compete
    from bank.agents.advanced_agents import (
        LeaderOnlyAgent,
        LeaderPlusFiveAgent,
        LeaderPlusFourAgent,
        LeaderPlusOneAgent,
        LeaderPlusSevenAgent,
        LeaderPlusSixAgent,
        LeaderPlusThreeAgent,
        LeaderPlusTwoAgent,
        LeechAgent,
        RankBasedAgent,
    )
    from bank.agents.threshold_agents import (
        threshold_250_agent,
        threshold_275_agent,
        threshold_300_agent,
        threshold_325_agent,
        threshold_350_agent,
        threshold_375_agent,
        threshold_400_agent,
        threshold_425_agent,
        threshold_450_agent,
        threshold_475_agent,
        threshold_500_agent,
        threshold_550_agent,
        threshold_600_agent,
    )

    agent_configs = [
        {"class": RandomAgent, "name": "Random", "kwargs": {"seed": 42}},
        {"class": ThresholdAgent, "name": "Threshold50", "kwargs": {"threshold": 50}},
        {"class": ThresholdAgent, "name": "Threshold80", "kwargs": {"threshold": 80}},
        {"class": ConservativeAgent, "name": "Conservative"},
        {"class": AggressiveAgent, "name": "Aggressive"},
        {"class": SmartAgent, "name": "Smart"},
        {"class": AdaptiveAgent, "name": "Adaptive"},
        {"class": LeaderOnlyAgent, "name": "LeaderOnly"},
        {"class": LeaderPlusOneAgent, "name": "LeaderPlusOne"},
        {"class": LeaderPlusTwoAgent, "name": "LeaderPlusTwo"},
        {"class": LeaderPlusThreeAgent, "name": "LeaderPlusThree"},
        {"class": LeaderPlusFourAgent, "name": "LeaderPlusFour"},
        {"class": LeaderPlusFiveAgent, "name": "LeaderPlusFive"},
        {"class": LeaderPlusSixAgent, "name": "LeaderPlusSix"},
        {"class": LeaderPlusSevenAgent, "name": "LeaderPlusSeven"},
        {"class": LeechAgent, "name": "Leech"},
        {"class": RankBasedAgent, "name": "RankBased"},
        {"class": threshold_250_agent, "name": "Threshold-250"},
        {"class": threshold_275_agent, "name": "Threshold-275"},
        {"class": threshold_300_agent, "name": "Threshold-300"},
        {"class": threshold_325_agent, "name": "Threshold-325"},
        {"class": threshold_350_agent, "name": "Threshold-350"},
        {"class": threshold_375_agent, "name": "Threshold-375"},
        {"class": threshold_400_agent, "name": "Threshold-400"},
        {"class": threshold_425_agent, "name": "Threshold-425"},
        {"class": threshold_450_agent, "name": "Threshold-450"},
        {"class": threshold_475_agent, "name": "Threshold-475"},
        {"class": threshold_500_agent, "name": "Threshold-500"},
        {"class": threshold_550_agent, "name": "Threshold-550"},
        {"class": threshold_600_agent, "name": "Threshold-600"},
    ]

    # Run tournament
    stats = run_tournament(agent_configs, num_games=num_games, num_rounds=num_rounds)

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


def main():
    parser = argparse.ArgumentParser(description="BANK! Tournament Runner")
    parser.add_argument("--games", type=int, default=1000, help="Number of games to run")
    parser.add_argument("--rounds", type=int, default=20, help="Number of rounds per game")
    args = parser.parse_args()

    compare_strategies(num_games=args.games, num_rounds=args.rounds)


if __name__ == "__main__":
    main()
