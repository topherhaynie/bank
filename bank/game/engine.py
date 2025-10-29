"""BANK! Game Engine - Dice variant.

Core game logic and rules implementation for the         if self.state.game_over:
            return

        # Determine round number
        round_number = (
            1
            if self.state.current_round is None
            else self.state.current_round.round_number + 1
        )ed BANK! game.
"""

import random

from bank.game.state import GameState, PlayerState, RoundState

# Constants for dice game rules
DICE_FACES = 6
NUM_DICE = 2
SEVEN_VALUE = 7
SEVEN_BONUS_POINTS = 70
DOUBLE_MULTIPLIER = 2
MIN_PLAYERS = 2


class BankGame:
    """Main game engine for BANK! dice game.

    This class handles the core game logic, rules, and state management
    for the dice-based variant of BANK!
    """

    def __init__(
        self,
        num_players: int = 2,
        player_names: list[str] | None = None,
        total_rounds: int = 10,
        rng: random.Random | None = None,
    ) -> None:
        """Initialize a new BANK! game.

        Args:
            num_players: Number of players (minimum 2)
            player_names: Optional list of player names
            total_rounds: Number of rounds to play (10, 15, or 20 recommended)
            rng: Optional Random instance for deterministic behavior

        """
        if num_players < MIN_PLAYERS:
            msg = f"Must have at least {MIN_PLAYERS} players"
            raise ValueError(msg)

        if player_names is None:
            player_names = [f"Player {i + 1}" for i in range(num_players)]
        elif len(player_names) != num_players:
            msg = "Number of names must match number of players"
            raise ValueError(msg)

        self.rng = rng if rng is not None else random.Random()
        self.state = self._initialize_game(player_names, total_rounds)

    def _initialize_game(
        self,
        player_names: list[str],
        total_rounds: int,
    ) -> GameState:
        """Initialize a new game state.

        Args:
            player_names: List of player names
            total_rounds: Total number of rounds to play

        Returns:
            Initialized GameState

        """
        players = [PlayerState(player_id=i, name=name) for i, name in enumerate(player_names)]

        return GameState(
            players=players,
            total_rounds=total_rounds,
            current_round=None,
            game_over=False,
            winner=None,
        )

    def start_new_round(self) -> None:
        """Start a new round of the game.

        Initializes a new RoundState and resets all players' banking status.
        """
        if self.state.game_over:
            return

        # Determine round number
        if self.state.current_round is None:
            round_number = 1
        else:
            round_number = self.state.current_round.round_number + 1

        # Reset all players' banking status
        for player in self.state.players:
            player.has_banked_this_round = False

        # Create new round with all players active
        active_player_ids = {p.player_id for p in self.state.players}

        self.state.current_round = RoundState(
            round_number=round_number,
            roll_count=0,
            current_bank=0,
            last_roll=None,
            active_player_ids=active_player_ids,
        )

    def roll_dice(self) -> tuple[int, int]:
        """Roll two six-sided dice.

        Returns:
            Tuple of (die1, die2) where each die is 1-6

        """
        die1 = self.rng.randint(1, DICE_FACES)
        die2 = self.rng.randint(1, DICE_FACES)
        return (die1, die2)

    def process_roll(self) -> tuple[int, int]:
        """Process a dice roll and update the game state.

        Returns:
            The dice roll result (die1, die2)

        """
        if not self.state.current_round:
            msg = "Cannot roll dice: no active round"
            raise RuntimeError(msg)

        if self.state.game_over:
            msg = "Cannot roll dice: game is over"
            raise RuntimeError(msg)

        # Roll the dice
        die1, die2 = self.roll_dice()
        dice_sum = die1 + die2

        # Update round state
        self.state.current_round.roll_count += 1
        self.state.current_round.last_roll = (die1, die2)

        # Determine if we're in first three rolls
        is_first_three = self.state.current_round.is_first_three_rolls()

        # Check for doubles
        is_double = die1 == die2

        # Apply bank accumulation rules
        if dice_sum == SEVEN_VALUE:
            if is_first_three:
                # Seven during first 3 rolls: add 70 points
                self.state.current_round.current_bank += SEVEN_BONUS_POINTS
            else:
                # Seven after first 3 rolls: end round, bank is lost
                self._end_round_on_seven()
        elif is_double and not is_first_three:
            # Doubles after first 3 rolls: double the bank
            self.state.current_round.current_bank *= DOUBLE_MULTIPLIER
        else:
            # Normal roll or doubles in first 3 rolls: add sum
            self.state.current_round.current_bank += dice_sum

        return (die1, die2)

    def player_banks(self, player_id: int) -> bool:
        """Process a player banking action.

        Args:
            player_id: ID of the player who wants to bank

        Returns:
            True if banking was successful, False otherwise

        """
        if not self.state.current_round:
            return False

        if self.state.game_over:
            return False

        # Check if player is in the game
        player = self.state.get_player(player_id)
        if not player:
            return False

        # Check if player is still active in this round
        if player_id not in self.state.current_round.active_player_ids:
            return False

        # Check if player has already banked
        if player.has_banked_this_round:
            return False

        # Transfer bank to player's score
        player.score += self.state.current_round.current_bank
        player.has_banked_this_round = True

        # Remove player from active players
        self.state.current_round.active_player_ids.discard(player_id)

        # Check if round should end (all players have banked)
        if len(self.state.current_round.active_player_ids) == 0:
            self._end_round_all_banked()

        return True

    def _end_round_on_seven(self) -> None:
        """End the round due to rolling a seven (after first 3 rolls).

        Bank is lost, no points awarded.
        """
        if not self.state.current_round:
            return

        # Bank is already lost (set to 0 implicitly by not awarding points)
        self.state.current_round.current_bank = 0

        # Check if game is over
        if self.state.current_round.round_number >= self.state.total_rounds:
            self._end_game()
        # Round will end naturally, next round will be started by caller

    def _end_round_all_banked(self) -> None:
        """End the round because all players have banked."""
        if not self.state.current_round:
            return

        # Check if game is over
        if self.state.current_round.round_number >= self.state.total_rounds:
            self._end_game()

    def is_round_over(self) -> bool:
        """Check if the current round is over.

        Returns:
            True if the round has ended

        """
        if not self.state.current_round:
            return True

        # Round is over if all players have banked
        if len(self.state.current_round.active_player_ids) == 0:
            return True

        # Round is over if seven was rolled (bank reset to 0) and at least one roll was made
        return self.state.current_round.current_bank == 0 and self.state.current_round.roll_count > 0

    def _end_game(self) -> None:
        """End the game and determine the winner."""
        self.state.game_over = True

        # Find winner (player with highest score)
        if self.state.players:
            winner = max(self.state.players, key=lambda p: p.score)
            self.state.winner = winner.player_id

    def get_active_players(self) -> list[PlayerState]:
        """Get list of players still active in the current round.

        Returns:
            List of active PlayerState objects

        """
        return self.state.get_active_players()

    def reset(self, seed: int | None = None) -> GameState:
        """Reset the game to initial state.

        Args:
            seed: Optional seed for RNG

        Returns:
            The reset GameState

        """
        if seed is not None:
            self.rng.seed(seed)

        player_names = [p.name for p in self.state.players]
        total_rounds = self.state.total_rounds

        self.state = self._initialize_game(player_names, total_rounds)
        return self.state

    def get_state(self) -> GameState:
        """Get the current game state.

        Returns:
            The current GameState

        """
        return self.state

    def is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            True if the game has ended

        """
        return self.state.game_over

    def get_winner(self) -> PlayerState | None:
        """Get the winning player if game is over.

        Returns:
            The winning PlayerState or None if game isn't over

        """
        if self.state.winner is not None:
            return self.state.get_player(self.state.winner)
        return None
