"""
Multi-Agent Tournament Example

This example shows how to run multiple games and collect statistics.
"""

from bank.game.engine import BankGame
from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import RuleBasedAgent
from bank.cli.game_runner import GameRunner
from collections import defaultdict


def run_tournament(agents, num_games=10):
    """
    Run a tournament between agents.
    
    Args:
        agents: List of agent classes to compete
        num_games: Number of games to play
        
    Returns:
        Dictionary of statistics
    """
    stats = defaultdict(lambda: {"wins": 0, "total_score": 0, "games": 0})
    
    print(f"\n{'=' * 60}")
    print(f"Running tournament: {num_games} games")
    print(f"{'=' * 60}\n")
    
    for game_num in range(num_games):
        print(f"Game {game_num + 1}/{num_games}...")
        
        # Create fresh game
        player_names = [agent.__class__.__name__ for agent in agents]
        game = BankGame(num_players=len(agents), player_names=player_names)
        
        # Create fresh agent instances for this game
        game_agents = [
            agent.__class__(player_id=i, name=f"{agent.__class__.__name__}")
            for i, agent in enumerate(agents)
        ]
        
        # Run game without delays
        runner = GameRunner(game, game_agents, delay=0)
        runner.run()
        
        # Collect statistics
        for player in game.state.players:
            agent_name = player.name
            stats[agent_name]["games"] += 1
            stats[agent_name]["total_score"] += player.score
            
            # Check if this player won
            winner = game.get_winner()
            if winner and winner.player_id == player.player_id:
                stats[agent_name]["wins"] += 1
    
    return stats


def print_tournament_results(stats):
    """Print tournament statistics."""
    print(f"\n{'=' * 60}")
    print("Tournament Results")
    print(f"{'=' * 60}\n")
    
    # Sort by wins
    sorted_agents = sorted(
        stats.items(),
        key=lambda x: (x[1]["wins"], x[1]["total_score"]),
        reverse=True
    )
    
    print(f"{'Agent':<20} {'Wins':<8} {'Avg Score':<12} {'Win Rate':<10}")
    print("-" * 60)
    
    for agent_name, agent_stats in sorted_agents:
        wins = agent_stats["wins"]
        games = agent_stats["games"]
        avg_score = agent_stats["total_score"] / games if games > 0 else 0
        win_rate = (wins / games * 100) if games > 0 else 0
        
        print(f"{agent_name:<20} {wins:<8} {avg_score:<12.2f} {win_rate:<10.1f}%")


def main():
    """Run a tournament between different agent types."""
    # Create agents to compete
    agents = [
        RandomAgent(player_id=0, name="Random", seed=42),
        RuleBasedAgent(player_id=1, name="RuleBased"),
    ]
    
    # Run tournament
    num_games = 20
    stats = run_tournament(agents, num_games=num_games)
    
    # Display results
    print_tournament_results(stats)


if __name__ == "__main__":
    main()
