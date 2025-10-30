"""Human Player Agent.

Interactive agent for human players via CLI for the BANK! dice game.
"""

import signal
from collections.abc import Generator
from contextlib import contextmanager

import click

from bank.agents.base import Action, Agent, Observation

# Constants for dice game rules
SEVEN_VALUE = 7
SPECIAL_ROLL_THRESHOLD = 3


class InputTimeoutError(Exception):
    """Raised when user input times out."""


@contextmanager
def timeout(seconds: int | None) -> Generator[None, None, None]:
    """Context manager for timing out user input.

    Args:
        seconds: Number of seconds before timeout, or None for no timeout

    Raises:
        InputTimeoutError: If the operation times out

    """
    if seconds is None:
        yield
        return

    def timeout_handler(_signum: int, _frame: object) -> None:
        msg = "Input timed out"
        raise InputTimeoutError(msg)

    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Cancel the alarm and restore old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class HumanPlayer(Agent):
    """Interactive human player that prompts for input via command line.

    Implements the Agent interface for the BANK! dice game, displaying
    game state and prompting for bank/pass decisions.
    """

    def __init__(
        self,
        player_id: int,
        name: str = "Human",
        timeout_seconds: int | None = None,
        *,
        verbose: bool = True,
    ) -> None:
        """Initialize the human player.

        Args:
            player_id: The player ID this agent controls
            name: The player's name
            timeout_seconds: Optional timeout for input in seconds (None = no timeout)
            verbose: Whether to display detailed game state

        """
        super().__init__(player_id, name)
        self.timeout_seconds = timeout_seconds
        self.verbose = verbose

    def act(self, observation: Observation) -> Action:
        """Prompt the human player to select bank or pass.

        Args:
            observation: Current game state observation

        Returns:
            Action: either "bank" or "pass"

        Raises:
            InputTimeoutError: If input times out

        """
        if self.verbose:
            self._display_observation(observation)

        # Build action options
        actions: list[Action] = ["pass"]
        if observation["can_bank"]:
            actions.insert(0, "bank")  # Bank first if available

        # Display options with game state and stats
        click.echo("\n" + "=" * 60)
        click.echo(f"{self.name}'s Decision")
        click.echo("=" * 60)

        # Game context
        click.echo(f"\n🎮 Round {observation['round_number']} | Roll #{observation['roll_count']}")

        # Last roll info
        if observation["last_roll"]:
            die1, die2 = observation["last_roll"]
            dice_sum = die1 + die2
            click.echo(f"🎲 Last Roll: [{die1}] [{die2}] = {dice_sum}")

            # Add roll commentary
            if dice_sum == SEVEN_VALUE:
                if observation["roll_count"] <= SPECIAL_ROLL_THRESHOLD:
                    click.echo("   💰 SEVEN! Added 70 points to bank")
                else:
                    click.echo("   💥 SEVEN would end round - bank lost!")
            elif die1 == die2:
                if observation["roll_count"] <= SPECIAL_ROLL_THRESHOLD:
                    click.echo(f"   🎯 DOUBLES! Added {dice_sum} points")
                else:
                    click.echo("   🎯 DOUBLES! Bank doubled!")
        else:
            click.echo("🎲 No roll yet this round")

        # Bank value
        click.echo(f"\n💰 Bank: {observation['current_bank']} points")
        active_count = len(observation["active_player_ids"])
        click.echo(f"⚡ Active players: {active_count}")

        # Show all players with their status
        click.echo("\n📊 Current Standings:")
        for pid, score in sorted(
            observation["all_player_scores"].items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            is_you = pid == observation["player_id"]
            is_active = pid in observation["active_player_ids"]

            # Status indicator
            if not is_active:
                status = "💰 BANKED"
            elif is_you:
                status = "👉 YOUR TURN"
            else:
                status = "⚡ ACTIVE"

            player_label = f"Player {pid + 1}" if not is_you else self.name
            click.echo(f"   {player_label:<20} {score:>4} pts  {status}")

        click.echo("\nAvailable actions:")
        for idx, action in enumerate(actions, 1):
            if action == "bank":
                new_score = observation["player_score"] + observation["current_bank"]
                click.echo(
                    f"  {idx}. {action.upper()} (take {observation['current_bank']} → total: {new_score} pts)",
                )
            else:
                click.echo(f"  {idx}. {action.upper()} (stay in round, risk losing bank)")

        # Get selection with optional timeout
        try:
            with timeout(self.timeout_seconds):
                choice = self._get_action_choice(len(actions))
                action = actions[choice - 1]
                click.echo(f"\n{self.name} chose: {action.upper()}")
                return action
        except InputTimeoutError:
            # Default to pass on timeout
            click.echo(f"\n⏱️  Time's up! {self.name} defaults to PASS")
            return "pass"

    def _get_action_choice(self, num_actions: int) -> int:
        """Get valid action choice from user.

        Args:
            num_actions: Number of available actions

        Returns:
            1-indexed choice number

        Raises:
            click.Abort: If user presses Ctrl+C to exit

        """
        while True:
            try:
                return click.prompt(
                    f"\nSelect action (1-{num_actions})",
                    type=click.IntRange(1, num_actions),
                )
            except click.Abort:
                # User pressed Ctrl+C - let it propagate to exit the program
                raise
            except ValueError:
                click.echo("Invalid choice. Please try again.")

    def _display_observation(self, obs: Observation) -> None:
        """Display current game observation to the player.

        Args:
            obs: The observation to display

        """
        click.echo("\n" + "=" * 60)
        click.echo(f"Round {obs['round_number']} - Roll #{obs['roll_count']}")
        click.echo("=" * 60)

        # Display last roll
        if obs["last_roll"]:
            die1, die2 = obs["last_roll"]
            dice_sum = die1 + die2
            click.echo(f"\n🎲 Last Roll: [{die1}] [{die2}] = {dice_sum}")

            # Add commentary about the roll
            if dice_sum == SEVEN_VALUE:
                if obs["roll_count"] <= SPECIAL_ROLL_THRESHOLD:
                    click.echo("   💰 SEVEN! Adds 70 points to the bank!")
                else:
                    click.echo("   💥 SEVEN! Round ends - bank is lost!")
            elif die1 == die2:
                if obs["roll_count"] <= SPECIAL_ROLL_THRESHOLD:
                    click.echo(f"   🎯 DOUBLES! Adds {dice_sum} points to the bank")
                else:
                    click.echo(f"   🎯 DOUBLES! Bank doubled to {obs['current_bank']}!")
        else:
            click.echo("\n🎲 No roll yet this round")

        # Display bank
        click.echo(f"\n💰 Current Bank: {obs['current_bank']} points")

        # Display player info
        click.echo(f"\n👤 {self.name} (You)")
        click.echo(f"   Score: {obs['player_score']} points")
        click.echo(f"   Can bank: {'Yes ✓' if obs['can_bank'] else 'No (already banked)'}")

        # Display other players
        if len(obs["all_player_scores"]) > 1:
            click.echo("\n👥 Other Players:")
            for pid, score in sorted(obs["all_player_scores"].items()):
                if pid != obs["player_id"]:
                    active_marker = "⚡" if pid in obs["active_player_ids"] else "💤"
                    click.echo(f"   {active_marker} Player {pid + 1}: {score} points")

        # Display active players count
        active_count = len(obs["active_player_ids"])
        click.echo(f"\n⚡ Active players in round: {active_count}")
