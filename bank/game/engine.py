"""BANK! Game Engine - Dice variant.

Core game logic and rules implementation for the BANK! dice game.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from bank.game.state import GameState, PlayerState, RoundState

if TYPE_CHECKING:
    from bank.agents.base import Action, Agent, Observation
    from bank.replay.recorder import GameRecorder

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
        agents: list[Agent] | None = None,
        deterministic_polling: bool = False,
        recorder: GameRecorder | None = None,
    ) -> None:
        """Initialize a new BANK! game.

        Args:
            num_players: Number of players (minimum 2)
            player_names: Optional list of player names
            total_rounds: Number of rounds to play (10, 15, or 20 recommended)
            rng: Optional Random instance for deterministic behavior
            agents: Optional list of Agent instances for automated decision making
            deterministic_polling: If True, poll agents sequentially in player ID order.
                If False (default), poll all agents simultaneously without revealing
                other players' decisions. Use True for testing when you need
                reproducible behavior.
            recorder: Optional GameRecorder instance for recording game events

        """
        if num_players < MIN_PLAYERS:
            msg = f"Must have at least {MIN_PLAYERS} players"
            raise ValueError(msg)

        if player_names is None:
            player_names = [f"Player {i + 1}" for i in range(num_players)]
        elif len(player_names) != num_players:
            msg = "Number of names must match number of players"
            raise ValueError(msg)

        if agents is not None and len(agents) != num_players:
            msg = "Number of agents must match number of players"
            raise ValueError(msg)

        self.rng = rng or random.Random()
        self.state = self._initialize_game(player_names, total_rounds)
        self.agents = agents
        self.deterministic_polling = deterministic_polling
        self.recorder = recorder

        # Record game start if recorder is provided
        if self.recorder:
            seed = getattr(self.rng, "_seed", None) if hasattr(self.rng, "_seed") else None
            self.recorder.start_game(
                num_players=num_players,
                player_names=player_names,
                total_rounds=total_rounds,
                seed=seed,
            )

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

        # Record round start if recorder is provided
        if self.recorder:
            self.recorder.record_round_start(round_number)

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

        # Store bank value before applying roll effects
        bank_before = self.state.current_round.current_bank

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

        # Record roll if recorder is provided
        if self.recorder:
            self.recorder.record_roll(
                round_number=self.state.current_round.round_number,
                roll_count=self.state.current_round.roll_count,
                dice=(die1, die2),
                bank_before=bank_before,
                bank_after=self.state.current_round.current_bank,
            )

        return (die1, die2)

    def create_observation(self, player_id: int) -> Observation:
        """Create an observation for a specific player.

        Args:
            player_id: ID of the player to create observation for

        Returns:
            Observation dictionary for the player

        """
        if not self.state.current_round:
            msg = "Cannot create observation: no active round"
            raise RuntimeError(msg)

        player = self.state.get_player(player_id)
        if not player:
            msg = f"Invalid player_id: {player_id}"
            raise ValueError(msg)

        # Import here to avoid circular dependency at module level
        from bank.agents.base import Observation

        return Observation(
            round_number=self.state.current_round.round_number,
            roll_count=self.state.current_round.roll_count,
            current_bank=self.state.current_round.current_bank,
            last_roll=self.state.current_round.last_roll,
            active_player_ids=self.state.current_round.active_player_ids.copy(),
            player_id=player_id,
            player_score=player.score,
            can_bank=not player.has_banked_this_round,
            all_player_scores={p.player_id: p.score for p in self.state.players},
        )

    def poll_decisions(self) -> list[int]:
        """Poll all active players for banking decisions.

        In async mode (default), all agents are polled simultaneously and don't
        see each other's decisions until after all decisions are collected.

        In deterministic mode, agents are queried sequentially in player ID order
        and each banking action is processed immediately before the next agent
        is queried. This mode is useful for testing.

        Returns:
            List of player IDs who banked during this poll

        """
        if not self.state.current_round:
            return []

        if not self.agents:
            # No agents configured, return empty list
            return []

        # Get active players who can still bank
        active_ids = [
            pid
            for pid in self.state.current_round.active_player_ids
            if not self.state.get_player(pid).has_banked_this_round  # type: ignore[union-attr]
        ]

        if self.deterministic_polling:
            # Sequential polling: process each decision immediately
            return self._poll_deterministic(sorted(active_ids))
        # Async polling: collect all decisions, then process simultaneously
        return self._poll_simultaneous(active_ids)

    def _poll_deterministic(self, active_ids: list[int]) -> list[int]:
        """Poll agents sequentially in order, processing each decision immediately.

        Args:
            active_ids: List of active player IDs (should be sorted)

        Returns:
            List of player IDs who banked

        """
        banked_players = []

        for player_id in active_ids:
            if player_id >= len(self.agents):  # type: ignore[arg-type]
                continue  # No agent for this player

            agent = self.agents[player_id]  # type: ignore[index]
            observation = self.create_observation(player_id)
            action: Action = agent.act(observation)

            if action == "bank":
                success = self.player_banks(player_id)
                if success:
                    banked_players.append(player_id)

        return banked_players

    def _poll_simultaneous(self, active_ids: list[int]) -> list[int]:
        """Poll all agents simultaneously and process all decisions together.

        All agents receive observations at the same bank state and make decisions
        without seeing other players' choices. This is more realistic gameplay.

        Args:
            active_ids: List of active player IDs

        Returns:
            List of player IDs who banked

        """
        # Collect all decisions without processing any yet
        decisions: dict[int, Action] = {}
        for player_id in active_ids:
            if player_id >= len(self.agents):  # type: ignore[arg-type]
                continue  # No agent for this player

            agent = self.agents[player_id]  # type: ignore[index]
            if agent is None:
                continue  # Agent slot is None (externally controlled)

            observation = self.create_observation(player_id)
            action: Action = agent.act(observation)
            decisions[player_id] = action

        # Now process all banking decisions together
        # Use sorted order for consistent results when multiple players bank
        banked_players = []
        for player_id in sorted(decisions.keys()):
            if decisions[player_id] == "bank":
                success = self.player_banks(player_id)
                if success:
                    banked_players.append(player_id)

        return banked_players

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

        # Store score before banking
        score_before = player.score

        # Transfer bank to player's score
        player.score += self.state.current_round.current_bank
        player.has_banked_this_round = True

        # Record banking action if recorder is provided
        if self.recorder:
            self.recorder.record_bank(
                round_number=self.state.current_round.round_number,
                player_id=player_id,
                player_name=player.name,
                amount=self.state.current_round.current_bank,
                score_before=score_before,
                score_after=player.score,
            )

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
        bank_amount = self.state.current_round.current_bank
        self.state.current_round.current_bank = 0

        # Record round end if recorder is provided
        if self.recorder:
            player_scores = {p.player_id: p.score for p in self.state.players}
            self.recorder.record_round_end(
                round_number=self.state.current_round.round_number,
                reason="seven_rolled",
                final_bank=bank_amount,
                player_scores=player_scores,
            )

        # Check if game is over
        if self.state.current_round.round_number >= self.state.total_rounds:
            self._end_game()
        # Round will end naturally, next round will be started by caller

    def _end_round_all_banked(self) -> None:
        """End the round because all players have banked."""
        if not self.state.current_round:
            return

        # Record round end if recorder is provided
        if self.recorder:
            player_scores = {p.player_id: p.score for p in self.state.players}
            self.recorder.record_round_end(
                round_number=self.state.current_round.round_number,
                reason="all_banked",
                final_bank=self.state.current_round.current_bank,
                player_scores=player_scores,
            )

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
        winner_ids = []
        winner_names = []
        if self.state.players:
            max_score = max(p.score for p in self.state.players)
            winners = [p for p in self.state.players if p.score == max_score]
            winner_ids = [w.player_id for w in winners]
            winner_names = [w.name for w in winners]
            # Set first winner as the winner (legacy single-winner field)
            self.state.winner = winners[0].player_id

        # Record game end if recorder is provided
        if self.recorder:
            final_scores = {p.player_id: p.score for p in self.state.players}
            self.recorder.record_game_end(
                final_scores=final_scores,
                winner_ids=winner_ids,
                winner_names=winner_names,
            )

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

    def play_game(self) -> GameState:
        """Play a complete game from start to finish.

        This method runs a full game by:
        1. Playing all rounds until total_rounds is reached
        2. For each round:
           - Rolling dice and processing bank accumulation
           - Polling agents for banking decisions
           - Continuing until round ends (all banked or seven rolled)
        3. Determining the winner

        Returns:
            The final GameState after all rounds are complete

        Raises:
            RuntimeError: If agents are not configured

        """
        if self.agents is None:
            msg = "Cannot play game without agents. Provide agents in constructor."
            raise RuntimeError(msg)

        # Play all rounds
        while not self.is_game_over():
            self.play_round()

        return self.state

    def play_round(self) -> None:
        """Play a single round to completion.

        This method:
        1. Starts a new round
        2. Repeatedly rolls dice and polls for banking decisions
        3. Continues until the round ends (all players banked or seven rolled)

        """
        self.start_new_round()

        # Keep rolling and polling until round is over
        while not self.is_round_over():
            # Roll dice and update bank
            self.process_roll()

            # Poll agents for banking decisions (if round not ended by seven)
            if not self.is_round_over():
                self.poll_decisions()
