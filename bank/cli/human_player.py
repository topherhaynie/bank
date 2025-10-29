"""
Human Player Agent

Interactive agent for human players via CLI.
"""

import click
from typing import Dict, Any, Tuple
from bank.game.state import GameState
from bank.agents.base import BaseAgent


class HumanPlayer(BaseAgent):
    """
    Interactive human player that prompts for input via command line.
    """
    
    def __init__(self, player_id: int, name: str = "Human"):
        """
        Initialize the human player.
        
        Args:
            player_id: The player ID this agent controls
            name: The player's name
        """
        super().__init__(player_id, name)
    
    def select_action(self, game_state: GameState, valid_actions: list) -> Tuple[str, Dict[str, Any]]:
        """
        Prompt the human player to select an action.
        
        Args:
            game_state: Current game state
            valid_actions: List of valid action names
            
        Returns:
            Tuple of (action_name, action_parameters)
        """
        player = game_state.players[self.player_id]
        
        click.echo("\n" + "=" * 50)
        click.echo(f"{self.name}'s Turn")
        click.echo("=" * 50)
        self._display_game_state(game_state)
        
        # Display valid actions
        click.echo("\nValid actions:")
        for idx, action in enumerate(valid_actions, 1):
            click.echo(f"  {idx}. {action}")
        
        # Get action selection
        while True:
            try:
                choice = click.prompt(
                    "\nSelect action",
                    type=click.IntRange(1, len(valid_actions))
                )
                action = valid_actions[choice - 1]
                break
            except (ValueError, IndexError):
                click.echo("Invalid choice. Please try again.")
        
        # Get action parameters
        params = {}
        if action in ["play_card", "bank_card"] and player.hand:
            click.echo("\nYour hand:")
            for idx, card in enumerate(player.hand):
                click.echo(f"  {idx + 1}. Card value: {card}")
            
            while True:
                try:
                    card_choice = click.prompt(
                        "Select card",
                        type=click.IntRange(1, len(player.hand))
                    )
                    params["card_idx"] = card_choice - 1
                    break
                except (ValueError, IndexError):
                    click.echo("Invalid choice. Please try again.")
        
        return (action, params)
    
    def _display_game_state(self, game_state: GameState) -> None:
        """Display current game state to the player."""
        click.echo(f"\nRound: {game_state.round_number}")
        click.echo(f"Deck: {len(game_state.deck)} cards remaining")
        click.echo(f"Discard pile: {len(game_state.discard_pile)} cards")
        
        click.echo("\nPlayers:")
        for p in game_state.players:
            marker = " <-- YOU" if p.player_id == self.player_id else ""
            click.echo(
                f"  {p.name}: Score={p.score}, "
                f"Hand={len(p.hand)}, Bank={len(p.bank)}{marker}"
            )
        
        player = game_state.players[self.player_id]
        click.echo(f"\nYour hand: {player.hand}")
        click.echo(f"Your bank: {player.bank}")
