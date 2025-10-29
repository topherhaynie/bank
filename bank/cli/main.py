"""
Main CLI Entry Point

Command-line interface for playing BANK!
"""

import click
from bank.game.engine import BankGame
from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import RuleBasedAgent
from bank.cli.human_player import HumanPlayer
from bank.cli.game_runner import GameRunner


@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    BANK! - A card game with AI agent support.
    
    Play against AI agents or watch agents compete against each other.
    """
    pass


@main.command()
@click.option("--players", "-p", default=2, help="Number of players (2-6)")
@click.option("--human", "-h", default=1, help="Number of human players")
@click.option("--random", "-r", default=0, help="Number of random AI players")
@click.option("--rule-based", "-rb", default=0, help="Number of rule-based AI players")
@click.option("--seed", "-s", type=int, default=None, help="Random seed for reproducibility")
def play(players, human, random, rule_based, seed):
    """Start a new game of BANK!"""
    
    total_agents = human + random + rule_based
    if total_agents != players:
        click.echo(f"Error: Number of agents ({total_agents}) must equal number of players ({players})")
        return
    
    if players < 2:
        click.echo("Error: Must have at least 2 players")
        return
    
    click.echo("=" * 50)
    click.echo("Welcome to BANK!")
    click.echo("=" * 50)
    click.echo()
    
    # Create agents
    agents = []
    agent_id = 0
    
    # Add human players
    for i in range(human):
        name = click.prompt(f"Enter name for Human Player {i+1}", default=f"Human {i+1}")
        agents.append(HumanPlayer(player_id=agent_id, name=name))
        agent_id += 1
    
    # Add random agents
    for i in range(random):
        agents.append(RandomAgent(player_id=agent_id, name=f"RandomBot {i+1}", seed=seed))
        agent_id += 1
    
    # Add rule-based agents
    for i in range(rule_based):
        agents.append(RuleBasedAgent(player_id=agent_id, name=f"RuleBot {i+1}"))
        agent_id += 1
    
    # Create and run game
    player_names = [agent.name for agent in agents]
    game = BankGame(num_players=players, player_names=player_names)
    runner = GameRunner(game, agents)
    
    runner.run()


@main.command()
def demo():
    """Run a demo game with AI agents only."""
    
    click.echo("=" * 50)
    click.echo("BANK! Demo - AI vs AI")
    click.echo("=" * 50)
    click.echo()
    
    # Create agents
    agents = [
        RandomAgent(player_id=0, name="RandomBot"),
        RuleBasedAgent(player_id=1, name="RuleBot"),
    ]
    
    # Create and run game
    player_names = [agent.name for agent in agents]
    game = BankGame(num_players=2, player_names=player_names)
    runner = GameRunner(game, agents)
    
    runner.run()
    
    click.echo("\nDemo complete!")


if __name__ == "__main__":
    main()
