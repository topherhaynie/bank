"""Main CLI Entry Point.

Command-line interface for playing BANK! dice game.
"""

import random

import click

from bank.agents.advanced_agents import (
    LeaderPlusFiveAgent,
    LeaderPlusFourAgent,
    LeaderPlusOneAgent,
    LeaderPlusSevenAgent,
    LeaderPlusSixAgent,
    LeaderPlusThreeAgent,
    LeaderPlusTwoAgent,
)
from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import (
    AdaptiveAgent,
    AggressiveAgent,
    ConservativeAgent,
    SmartAgent,
    ThresholdAgent,
)
from bank.cli.game_runner import GameRunner
from bank.cli.human_player import HumanPlayer
from bank.game.engine import BankGame


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """BANK! - A dice game with AI agent support.

    Play against AI agents or watch agents compete against each other.
    """


@main.command()
@click.option("--players", "-p", default=2, help="Number of players (minimum 2)")
@click.option("--rounds", "-r", default=10, help="Number of rounds (recommended: 10, 15, or 20)")
@click.option("--human", "-h", default=1, help="Number of human players")
@click.option("--random", default=0, help="Number of random AI players")
@click.option("--threshold", "-t", default=0, help="Number of threshold-based AI players")
@click.option("--conservative", "-c", default=0, help="Number of conservative AI players")
@click.option("--aggressive", "-a", default=0, help="Number of aggressive AI players")
@click.option("--smart", "-s", default=0, help="Number of smart AI players")
@click.option("--adaptive", default=0, help="Number of adaptive AI players")
@click.option("--leaderplus1", default=0, help="Number of LeaderPlusOne agents")
@click.option("--leaderplus2", default=0, help="Number of LeaderPlusTwo agents")
@click.option("--leaderplus3", default=0, help="Number of LeaderPlusThree agents")
@click.option("--leaderplus4", default=0, help="Number of LeaderPlusFour agents")
@click.option("--leaderplus5", default=0, help="Number of LeaderPlusFive agents")
@click.option("--leaderplus6", default=0, help="Number of LeaderPlusSix agents")
@click.option("--leaderplus7", default=0, help="Number of LeaderPlusSeven agents")
@click.option("--seed", type=int, default=None, help="Random seed for reproducibility")
@click.option("--timeout", type=int, default=None, help="Timeout for human input (seconds)")
@click.option("--delay", type=float, default=0.5, help="Delay between displays (seconds)")
def play(  # noqa: PLR0913
    players: int,
    rounds: int,
    human: int,
    random: int,
    threshold: int,
    conservative: int,
    aggressive: int,
    smart: int,
    adaptive: int,
    leaderplus1: int,
    leaderplus2: int,
    leaderplus3: int,
    leaderplus4: int,
    leaderplus5: int,
    leaderplus6: int,
    leaderplus7: int,
    seed: int | None,
    timeout: int | None,
    delay: float,
) -> None:
    """Start a new game of BANK!"""
    # Validate agent counts
    total_agents = (
        human
        + random
        + threshold
        + conservative
        + aggressive
        + smart
        + adaptive
        + leaderplus1
        + leaderplus2
        + leaderplus3
        + leaderplus4
        + leaderplus5
        + leaderplus6
        + leaderplus7
    )
    if total_agents != players:
        click.echo(
            f"Error: Number of agents ({total_agents}) must equal number of players ({players})",
        )
        return

    if players < 2:  # noqa: PLR2004
        click.echo("Error: Must have at least 2 players")
        return

    # Create RNG for game
    game_rng = None if seed is None else random.Random(seed)

    # Create agents
    agents = []
    agent_id = 0

    # Add human players
    for i in range(human):
        if human == 1:
            name = click.prompt("Enter your name", default="Human")
        else:
            name = click.prompt(f"Enter name for Player {i + 1}", default=f"Human {i + 1}")
        agents.append(HumanPlayer(player_id=agent_id, name=name, timeout_seconds=timeout))
        agent_id += 1

    # Add random agents
    for i in range(random):
        agent_seed = None if seed is None else seed + agent_id
        agents.append(
            RandomAgent(
                player_id=agent_id,
                name=f"RandomBot {i + 1}",
                seed=agent_seed,
            ),
        )
        agent_id += 1

    # Add threshold agents
    for i in range(threshold):
        agents.append(ThresholdAgent(player_id=agent_id, name=f"ThresholdBot {i + 1}"))
        agent_id += 1

    # Add conservative agents
    for i in range(conservative):
        agents.append(ConservativeAgent(player_id=agent_id, name=f"ConservativeBot {i + 1}"))
        agent_id += 1

    # Add aggressive agents
    for i in range(aggressive):
        agents.append(AggressiveAgent(player_id=agent_id, name=f"AggressiveBot {i + 1}"))
        agent_id += 1

    # Add smart agents
    for i in range(smart):
        agents.append(SmartAgent(player_id=agent_id, name=f"SmartBot {i + 1}"))
        agent_id += 1

    # Add adaptive agents
    for i in range(adaptive):
        agents.append(AdaptiveAgent(player_id=agent_id, name=f"AdaptiveBot {i + 1}"))
        agent_id += 1

    # Add LeaderPlusN agents
    for i in range(leaderplus1):
        agents.append(LeaderPlusOneAgent(player_id=agent_id, name=f"LeaderPlus1-{i + 1}"))
        agent_id += 1
    for i in range(leaderplus2):
        agents.append(LeaderPlusTwoAgent(player_id=agent_id, name=f"LeaderPlus2-{i + 1}"))
        agent_id += 1
    for i in range(leaderplus3):
        agents.append(LeaderPlusThreeAgent(player_id=agent_id, name=f"LeaderPlus3-{i + 1}"))
        agent_id += 1
    for i in range(leaderplus4):
        agents.append(LeaderPlusFourAgent(player_id=agent_id, name=f"LeaderPlus4-{i + 1}"))
        agent_id += 1
    for i in range(leaderplus5):
        agents.append(LeaderPlusFiveAgent(player_id=agent_id, name=f"LeaderPlus5-{i + 1}"))
        agent_id += 1
    for i in range(leaderplus6):
        agents.append(LeaderPlusSixAgent(player_id=agent_id, name=f"LeaderPlus6-{i + 1}"))
        agent_id += 1
    for i in range(leaderplus7):
        agents.append(LeaderPlusSevenAgent(player_id=agent_id, name=f"LeaderPlus7-{i + 1}"))
        agent_id += 1

    # Create and run game
    player_names = [agent.name for agent in agents]
    game = BankGame(
        num_players=players,
        player_names=player_names,
        total_rounds=rounds,
        rng=game_rng,
        agents=agents,
    )
    runner = GameRunner(game, agents, delay=delay)

    runner.run()


@main.command()
@click.option("--rounds", "-r", default=10, help="Number of rounds")
@click.option("--seed", type=int, default=None, help="Random seed for reproducibility")
@click.option("--delay", type=float, default=0.3, help="Delay between displays (seconds)")
def demo(rounds: int, seed: int | None, delay: float) -> None:
    """Run a demo game with AI agents only."""
    click.echo("\n" + "=" * 60)
    click.echo("BANK! Demo - AI Battle")
    click.echo("=" * 60)
    click.echo()

    # Create RNG for game
    game_rng = None if seed is None else random.Random(seed)

    # Create agents with different strategies
    agents = [
        RandomAgent(
            player_id=0,
            name="RandomBot",
            seed=seed,
        ),
        ThresholdAgent(player_id=1, name="ThresholdBot"),
        ConservativeAgent(player_id=2, name="ConservativeBot"),
        SmartAgent(player_id=3, name="SmartBot"),
    ]

    # Create and run game
    player_names = [agent.name for agent in agents]
    game = BankGame(
        num_players=4,
        player_names=player_names,
        total_rounds=rounds,
        rng=game_rng,
        agents=agents,
    )
    runner = GameRunner(game, agents, delay=delay)

    runner.run()

    click.echo("\nDemo complete!")


@main.command()
@click.argument("num_games", type=int, default=100)
@click.option("--rounds", "-r", default=10, help="Number of rounds per game")
@click.option("--seed", type=int, default=None, help="Random seed for reproducibility")
def tournament(num_games: int, rounds: int, seed: int | None) -> None:
    """Run a tournament between different agent strategies.

    NUM_GAMES: Number of games to play (default: 100)
    """
    click.echo("\n" + "=" * 60)
    click.echo(f"BANK! Tournament - {num_games} games")
    click.echo("=" * 60)
    click.echo()

    # Agent types to compete
    agent_configs = [
        ("RandomBot", lambda pid: RandomAgent(player_id=pid, name="RandomBot")),
        ("ThresholdBot", lambda pid: ThresholdAgent(player_id=pid, name="ThresholdBot")),
        (
            "ConservativeBot",
            lambda pid: ConservativeAgent(player_id=pid, name="ConservativeBot"),
        ),
        ("AggressiveBot", lambda pid: AggressiveAgent(player_id=pid, name="AggressiveBot")),
        ("SmartBot", lambda pid: SmartAgent(player_id=pid, name="SmartBot")),
        ("AdaptiveBot", lambda pid: AdaptiveAgent(player_id=pid, name="AdaptiveBot")),
    ]

    # Track wins
    wins = {name: 0 for name, _ in agent_configs}
    total_scores = {name: 0 for name, _ in agent_configs}

    # Run tournament
    with click.progressbar(range(num_games), label="Playing games") as bar:
        for game_num in bar:
            # Create agents
            game_seed = None if seed is None else seed + game_num
            game_rng = None if game_seed is None else random.Random(game_seed)

            agents = [factory(i) for i, (_, factory) in enumerate(agent_configs)]

            # Create and run game silently
            player_names = [agent.name for agent in agents]
            game = BankGame(
                num_players=len(agents),
                player_names=player_names,
                total_rounds=rounds,
                rng=game_rng,
                agents=agents,
            )

            # Run game silently (just use play_game)
            game.play_game()

            # Record results
            max_score = max(p.score for p in game.state.players)
            for player in game.state.players:
                agent_name = agent_configs[player.player_id][0]
                total_scores[agent_name] += player.score
                if player.score == max_score:
                    wins[agent_name] += 1

    # Display results
    click.echo("\n" + "=" * 60)
    click.echo("Tournament Results")
    click.echo("=" * 60)
    click.echo()

    # Sort by wins
    sorted_results = sorted(wins.items(), key=lambda x: x[1], reverse=True)

    click.echo(f"{'Agent':<20} {'Wins':<10} {'Avg Score':<10} {'Win Rate'}")
    click.echo("-" * 60)

    for name, win_count in sorted_results:
        avg_score = total_scores[name] / num_games
        win_rate = (win_count / num_games) * 100
        click.echo(f"{name:<20} {win_count:<10} {avg_score:<10.1f} {win_rate:.1f}%")

    click.echo()


if __name__ == "__main__":
    main()
