"""
Game Runner

Orchestrates game execution with multiple agents.
"""

import click
import time
from typing import List
from bank.game.engine import BankGame
from bank.agents.base import BaseAgent
from bank.cli.human_player import HumanPlayer


class GameRunner:
    """
    Manages game execution with multiple agents.
    
    Handles turn order, agent communication, and game flow.
    """
    
    def __init__(self, game: BankGame, agents: List[BaseAgent], delay: float = 0.5):
        """
        Initialize the game runner.
        
        Args:
            game: The game instance
            agents: List of agents (one per player)
            delay: Delay between AI turns for visibility (seconds)
        """
        self.game = game
        self.agents = agents
        self.delay = delay
        
        if len(agents) != game.state.num_players:
            raise ValueError("Number of agents must match number of players")
    
    def run(self) -> None:
        """Run the game to completion."""
        # Notify agents of game start
        for agent in self.agents:
            agent.on_game_start(self.game.state)
        
        click.echo("\nGame starting!")
        click.echo()
        
        turn_count = 0
        max_turns = 1000  # Prevent infinite loops
        
        while not self.game.is_game_over() and turn_count < max_turns:
            self._run_turn()
            turn_count += 1
        
        self._display_results()
    
    def _run_turn(self) -> None:
        """Execute a single turn."""
        current_idx = self.game.state.current_player_idx
        agent = self.agents[current_idx]
        
        # Notify agent of turn start
        agent.on_turn_start(self.game.state)
        
        # Add delay for AI agents (not for humans)
        if not isinstance(agent, HumanPlayer) and self.delay > 0:
            time.sleep(self.delay)
        
        # Get valid actions
        valid_actions = self.game.get_valid_actions()
        
        if not valid_actions:
            click.echo(f"{agent.name} has no valid actions. Skipping turn.")
            self.game.state.current_player_idx = (
                (self.game.state.current_player_idx + 1) % self.game.state.num_players
            )
            return
        
        # Get action from agent
        action, params = agent.select_action(self.game.state, valid_actions)
        
        # Display action for non-human players
        if not isinstance(agent, HumanPlayer):
            click.echo(f"{agent.name} performs: {action} {params}")
        
        # Execute action
        success = self.game.take_action(action, **params)
        
        if not success:
            click.echo(f"Warning: Action {action} failed for {agent.name}")
        
        # Notify agent of turn end
        agent.on_turn_end(self.game.state)
    
    def _display_results(self) -> None:
        """Display final game results."""
        click.echo("\n" + "=" * 50)
        click.echo("GAME OVER")
        click.echo("=" * 50)
        click.echo()
        
        # Display final scores
        click.echo("Final Scores:")
        sorted_players = sorted(
            self.game.state.players,
            key=lambda p: p.score,
            reverse=True
        )
        
        for rank, player in enumerate(sorted_players, 1):
            marker = " 🏆" if rank == 1 else ""
            click.echo(f"  {rank}. {player.name}: {player.score} points{marker}")
        
        # Notify agents of game end
        winner = self.game.get_winner()
        if winner:
            click.echo(f"\nWinner: {winner.name}!")
            for agent in self.agents:
                won = agent.player_id == winner.player_id
                agent.on_game_end(self.game.state, won)
        else:
            click.echo("\nGame ended in a draw!")
