"""Game Runner.

Orchestrates game execution with multiple agents for the BANK! dice game.
"""

import time

import click

from bank.agents.base import Agent
from bank.game.engine import BankGame


class GameRunner:
    """Manages game execution with multiple agents.

    Handles game flow display, agent coordination, and result presentation.
    """

    def __init__(
        self,
        game: BankGame,
        agents: list[Agent],
        delay: float = 0.5,
        *,
        verbose: bool = True,
    ) -> None:
        """Initialize the game runner.

        Args:
            game: The game instance
            agents: List of agents (one per player)
            delay: Delay between displays for readability (seconds)
            verbose: Whether to display detailed game flow

        Raises:
            ValueError: If number of agents doesn't match number of players

        """
        if len(agents) != game.state.num_players:
            msg = "Number of agents must match number of players"
            raise ValueError(msg)

        self.game = game
        self.agents = agents
        self.delay = delay
        self.verbose = verbose

    def run(self) -> dict[int, int]:
        """Run the game to completion.

        Returns:
            Dictionary mapping player_id to final score

        """
        self._display_header()

        # Reset all agents
        for agent in self.agents:
            agent.reset()

        # Run the game using the engine's play_game method
        # We'll hook into the game flow by displaying state periodically
        self._run_with_display()

        return self._display_results()

    def _display_header(self) -> None:
        """Display game start header."""
        click.echo("\n" + "=" * 60)
        click.echo("🎲 BANK! DICE GAME 🎲")
        click.echo("=" * 60)
        click.echo(f"\nPlayers: {self.game.state.num_players}")
        click.echo(f"Rounds: {self.game.state.total_rounds}")
        click.echo("\nPlayers:")
        for i, player in enumerate(self.game.state.players):
            agent_type = type(self.agents[i]).__name__
            click.echo(f"  {i + 1}. {player.name} ({agent_type})")
        click.echo()

        if self.delay > 0:
            time.sleep(self.delay)

    def _run_with_display(self) -> None:
        """Run the game with visual display of progress."""
        # Simply use the engine's play_game method
        # The engine handles all the game logic correctly
        self.game.play_game()

        # NOTE: Currently runs game silently and shows only final results
        # Future enhancement: add display hooks to engine for real-time updates

    def _display_round_start(self, round_num: int) -> None:
        """Display round start banner.

        Args:
            round_num: The round number starting

        """
        if self.verbose:
            click.echo("\n" + "🎲" * 30)
            click.echo(f"ROUND {round_num}")
            click.echo("🎲" * 30)

            if self.delay > 0:
                time.sleep(self.delay * 0.5)

    def _play_round_with_display(self) -> None:
        """Play a single round with display of dice rolls and decisions."""
        while not self.game.is_round_over():
            # Roll dice
            self.game.roll_dice()

            if self.verbose:
                self._display_roll()

            if self.delay > 0:
                time.sleep(self.delay)

            # Check if round ended from roll (e.g., seven after roll 3)
            if self.game.is_round_over():
                break

            # Poll decisions (returns list of player IDs who banked)
            banked_players = self.game.poll_decisions()

            if self.verbose:
                self._display_decisions(banked_players)

            if self.delay > 0:
                time.sleep(self.delay)

    def _display_roll(self) -> None:
        """Display the most recent dice roll."""
        if not self.game.state.current_round:
            return

        roll = self.game.state.current_round.last_roll
        if not roll:
            return

        die1, die2 = roll
        total = die1 + die2
        roll_num = self.game.state.current_round.roll_count
        bank = self.game.state.current_round.current_bank

        click.echo(f"\n🎲 Roll #{roll_num}: [{die1}] [{die2}] = {total}")

        # Add commentary
        if total == 7:  # noqa: PLR2004
            if roll_num <= 3:  # noqa: PLR2004
                click.echo("   💰 SEVEN! Added 70 points to bank")
            else:
                click.echo("   💥 SEVEN! Round over - bank lost!")
        elif die1 == die2:
            if roll_num <= 3:  # noqa: PLR2004
                click.echo(f"   🎯 DOUBLES! Added {total} points")
            else:
                click.echo("   🎯 DOUBLES! Bank doubled!")

        click.echo(f"   Bank now: {bank} points")

    def _display_decisions(self, banked_players: list[int]) -> None:
        """Display player decisions.

        Args:
            banked_players: List of player IDs who banked

        """
        if not self.game.state.current_round:
            return

        # Get all players who were active before this decision round
        # Note: banked_players have already been removed from active_player_ids
        active_before = self.game.state.current_round.active_player_ids | set(banked_players)

        if not active_before:
            return

        click.echo("\n📋 Player Decisions:")

        # Show who banked
        for player_id in sorted(banked_players):
            player = self.game.state.players[player_id]
            click.echo(f"   💰 {player.name}: BANK")

        # Show who passed (those still active after decisions)
        for player_id in sorted(self.game.state.current_round.active_player_ids):
            player = self.game.state.players[player_id]
            click.echo(f"   ➡️  {player.name}: PASS")

    def _display_round_end(self) -> None:
        """Display end of round summary."""
        if not self.verbose or not self.game.state.current_round:
            return

        click.echo("\n" + "-" * 60)
        click.echo("Round Complete!")
        click.echo("\nCurrent Scores:")

        # Sort by score descending
        sorted_players = sorted(
            self.game.state.players,
            key=lambda p: p.score,
            reverse=True,
        )

        for player in sorted_players:
            click.echo(f"  {player.name}: {player.score} points")

        click.echo("-" * 60)

        if self.delay > 0:
            time.sleep(self.delay)

    def _display_results(self) -> dict[int, int]:
        """Display final game results.

        Returns:
            Dictionary mapping player_id to final score

        """
        click.echo("\n" + "=" * 60)
        click.echo("🏆 GAME OVER 🏆")
        click.echo("=" * 60)

        # Sort players by score
        sorted_players = sorted(
            self.game.state.players,
            key=lambda p: p.score,
            reverse=True,
        )

        click.echo("\nFinal Standings:")
        for rank, player in enumerate(sorted_players, 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "  # noqa: PLR2004
            click.echo(f"  {medal} {rank}. {player.name}: {player.score} points")

        # Find winner(s)
        max_score = sorted_players[0].score
        winners = [p for p in sorted_players if p.score == max_score]

        if len(winners) == 1:
            click.echo(f"\n🎉 Winner: {winners[0].name}! 🎉")
        else:
            winner_names = ", ".join(w.name for w in winners)
            click.echo(f"\n🤝 Tie between: {winner_names}")

        click.echo()

        # Return final scores
        return {p.player_id: p.score for p in self.game.state.players}
