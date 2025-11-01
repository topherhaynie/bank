"""Gymnasium Environment Wrapper for BANK! dice game.

This module wraps the BANK! game engine for reinforcement learning training.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces

    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False
    gym = None
    spaces = None

if TYPE_CHECKING:
    from bank.agents.base import Agent, Observation

from bank.agents.advanced_agents import (
    LeaderOnlyAgent,
    LeaderPlusOneAgent,
    LeechAgent,
    RankBasedAgent,
)
from bank.agents.random_agent import RandomAgent
from bank.agents.rule_based import (
    AdaptiveAgent,
    AggressiveAgent,
    ConservativeAgent,
    SmartAgent,
)
from bank.game.engine import BankGame


def flatten_observation(obs: Observation, total_rounds: int = 10) -> np.ndarray:
    """Convert Observation TypedDict to flat 14-feature vector.

    All features are normalized using tanh squashing for robust bounded output.
    Most features map to roughly [-1, 1] with typical values in [-0.5, 0.5] range.

    Features (all bounded to [-1, 1] via tanh):
        0. round_number / total_rounds - Game progress (exact: [0, 1])
        1. tanh(roll_count / 5.0) - Rolls this round (5 rolls → 0.76)
        2. tanh(current_bank / 250.0) - Points in bank (250 → 0.76, 500 → 0.95)
        3. die1 / 6.0 - First die value (exact: [0, 1]) or 0 if no roll
        4. die2 / 6.0 - Second die value (exact: [0, 1]) or 0 if no roll
        5. is_first_three - Binary flag (exact: {0, 1})
        6. tanh(player_score / 500.0) - Agent's score (500 → 0.76, 1000 → 0.96)
        7. can_bank - Binary flag (exact: {0, 1})
        8. num_active / num_players - Active players ratio (exact: [0, 1])
        9. tanh(avg_opponent / 500.0) - Average opponent score
        10. tanh(max_opponent / 500.0) - Best opponent score
        11. tanh(min_opponent / 500.0) - Worst opponent score
        12. is_leading - Binary flag (exact: {0, 1})
        13. tanh(score_gap / 500.0) - Gap to leader (centered at 0)
            (-500 → -0.76, 0 → 0.0, +500 → 0.76)

    The tanh normalization ensures:
    - Typical gameplay values stay in linear region (good gradient flow)
    - Extreme values are smoothly saturated (no hard clipping)
    - All features bounded to [-1, 1] (network stability)

    Args:
        obs: Observation dictionary from game engine
        total_rounds: Total rounds in game (for normalization)

    Returns:
        14-element numpy array with dtype float32

    """
    # Extract dice values (already naturally bounded [0, 1])
    if obs["last_roll"] is not None:
        die1 = float(obs["last_roll"][0]) / 6.0
        die2 = float(obs["last_roll"][1]) / 6.0
    else:
        die1 = 0.0
        die2 = 0.0

    # Extract player info
    player_score = float(obs["player_score"])
    all_scores = obs["all_player_scores"]
    opponent_scores = [float(score) for pid, score in all_scores.items() if pid != obs["player_id"]]

    # Compute opponent statistics
    if opponent_scores:
        avg_opponent = float(np.mean(opponent_scores))
        max_opponent = float(max(opponent_scores))
        min_opponent = float(min(opponent_scores))
        is_leading = 1.0 if player_score > max_opponent else 0.0
        score_gap = player_score - max_opponent
    else:
        # Single player edge case
        avg_opponent = 0.0
        max_opponent = 0.0
        min_opponent = 0.0
        is_leading = 1.0
        score_gap = 0.0

    # Total players for normalization
    num_players = len(all_scores)
    num_active = len(obs["active_player_ids"])

    # Build feature vector with tanh normalization for unbounded features
    features = np.array(
        [
            float(obs["round_number"]) / float(total_rounds),  # Exact [0, 1]
            np.tanh(float(obs["roll_count"]) / 7.0),  # ~7 rolls typical
            np.tanh(float(obs["current_bank"]) / 250.0),  # ~250 typical, 500 high
            die1,  # Exact [0, 1]
            die2,  # Exact [0, 1]
            1.0 if obs["roll_count"] <= 3 else 0.0,  # Exact {0, 1}
            np.tanh(player_score / 500.0),  # ~500 typical, 1000+ high
            1.0 if obs["can_bank"] else 0.0,  # Exact {0, 1}
            float(num_active) / float(num_players),  # Exact [0, 1]
            np.tanh(avg_opponent / 500.0),  # ~500 typical
            np.tanh(max_opponent / 500.0),  # ~500 typical
            np.tanh(min_opponent / 500.0),  # ~500 typical
            is_leading,  # Exact {0, 1}
            np.tanh(score_gap / 500.0),  # Centered at 0, ±500 is ±0.76
        ],
        dtype=np.float32,
    )

    return features


class BankEnv:
    """Gymnasium-compatible environment for BANK! dice game.

    This environment wraps the BANK! game engine for reinforcement learning.
    The learning agent is always player 0, and competes against opponent agents.

    Attributes:
        observation_space: 14-dimensional continuous space [-1, 1]
            Uses tanh normalization for robust bounded features
        action_space: Discrete(2) - 0=pass, 1=bank
        num_opponents: Number of opponent agents (1-5)
        total_rounds: Rounds per game
        reward_scheme: "sparse" or "tournament"
        tournament_size: Games per tournament (if using tournament scheme)

    """

    def __init__(
        self,
        num_opponents: int = 3,
        opponent_types: list[str] | None = None,
        total_rounds: int = 10,
        rng: random.Random | None = None,
        reward_scheme: str = "sparse",
        tournament_size: int = 5,
        tournament_win_weight: float = 2.0,
        tournament_rank_weight: float = 1.0,
        tournament_consistency_weight: float = 0.5,
        tournament_consistency_threshold: float = 0.5,
    ) -> None:
        """Initialize the BANK! environment.

        Args:
            num_opponents: Number of opponent agents (1-5)
            opponent_types: List of opponent types for each opponent
                Options: "random", "conservative", "aggressive", "smart",
                        "adaptive", "leader_only", "leader_plus_one",
                        "leech", "rank_based"
                If None, randomly selects for each opponent
            total_rounds: Number of rounds per game
            rng: Random number generator for determinism
            reward_scheme: Reward calculation method
                - "sparse": Simple win/loss (±1)
                - "tournament": Accumulate results over N games, reward based on
                  win rate, average rank, and consistency
            tournament_size: Number of games per tournament (for tournament scheme)
            tournament_win_weight: Weight for win rate component
            tournament_rank_weight: Weight for rank component (normalized)
            tournament_consistency_weight: Weight for consistency bonus
            tournament_consistency_threshold: Std dev threshold for consistency bonus

        Raises:
            ImportError: If gymnasium is not installed
            ValueError: If parameters are invalid

        """
        if not GYMNASIUM_AVAILABLE:
            msg = "Gymnasium is required for training. Install with: pip install gymnasium"
            raise ImportError(msg)

        # Validate parameters
        if num_opponents < 1 or num_opponents > 5:
            msg = f"num_opponents must be 1-5, got {num_opponents}"
            raise ValueError(msg)

        if total_rounds < 1:
            msg = f"total_rounds must be >= 1, got {total_rounds}"
            raise ValueError(msg)

        # Store config
        self.num_opponents = num_opponents
        self.total_rounds = total_rounds
        self.rng = rng or random.Random()

        # Store opponent types (will be used in reset)
        self.opponent_types = opponent_types

        # Reward calculation configuration
        if reward_scheme not in {"sparse", "tournament"}:
            msg = f"reward_scheme must be 'sparse' or 'tournament', got '{reward_scheme}'"
            raise ValueError(msg)

        self.reward_scheme = reward_scheme
        self.tournament_size = tournament_size
        self.tournament_win_weight = tournament_win_weight
        self.tournament_rank_weight = tournament_rank_weight
        self.tournament_consistency_weight = tournament_consistency_weight
        self.tournament_consistency_threshold = tournament_consistency_threshold

        # Tournament tracking (if using tournament scheme)
        self.tournament_results: list[dict[str, Any]] = []
        self.current_tournament_game = 0

        # Define Gymnasium spaces
        # Note: Most features are in [-1, 1] range due to tanh normalization
        # Some features (round_number, dice, binary flags) are naturally [0, 1]
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(14,),
            dtype=np.float32,
        )

        # Action: 0=pass, 1=bank
        self.action_space = spaces.Discrete(2)

        # Game state (initialized in reset)
        self.game: BankGame | None = None
        self.learning_agent_id = 0  # Always player 0

    def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset environment for a new episode.

        Args:
            seed: Random seed for reproducibility
            options: Additional options (unused)

        Returns:
            Tuple of (observation, info_dict)

        """
        if seed is not None:
            self.rng.seed(seed)

        # Create opponent agents
        opponent_agents = self._create_opponent_agents()

        # Create all agents (learning agent + opponents)
        # Learning agent slot will be None - controlled externally
        all_agents: list[Agent | None] = [None] + opponent_agents

        # Create game
        self.game = BankGame(
            num_players=1 + self.num_opponents,
            agents=all_agents,
            total_rounds=self.total_rounds,
            rng=self.rng,
            deterministic_polling=False,  # Simultaneous polling
        )

        # Start first round
        self.game.start_new_round()

        # Get initial observation for learning agent
        obs = self.game.create_observation(self.learning_agent_id)
        flat_obs = flatten_observation(obs, self.total_rounds)

        info: dict[str, Any] = {}

        return flat_obs, info

    def _create_opponent_agents(self) -> list[Agent]:
        """Create opponent agents based on configuration.

        Returns:
            List of opponent Agent instances

        """
        from bank.agents.base import Agent as AgentType

        opponents: list[AgentType] = []

        # Available agent types
        agent_types = [
            "random",
            "conservative",
            "aggressive",
            "smart",
            "adaptive",
            "leader_only",
            "leader_plus_one",
            "leech",
            "rank_based",
        ]

        for i in range(self.num_opponents):
            # Player ID is 1-indexed (0 is learning agent)
            player_id = i + 1

            # Select opponent type
            if self.opponent_types and i < len(self.opponent_types):
                opponent_type = self.opponent_types[i]
            else:
                # Random selection
                opponent_type = self.rng.choice(agent_types)

            # Create agent
            agent: AgentType
            if opponent_type == "random":
                agent = RandomAgent(player_id, seed=self.rng.randint(0, 1_000_000))
            elif opponent_type == "conservative":
                agent = ConservativeAgent(player_id)
            elif opponent_type == "aggressive":
                agent = AggressiveAgent(player_id)
            elif opponent_type == "smart":
                agent = SmartAgent(player_id)
            elif opponent_type == "adaptive":
                agent = AdaptiveAgent(player_id)
            elif opponent_type == "leader_only":
                agent = LeaderOnlyAgent(player_id)
            elif opponent_type == "leader_plus_one":
                agent = LeaderPlusOneAgent(player_id)
            elif opponent_type == "leech":
                agent = LeechAgent(player_id)
            elif opponent_type == "rank_based":
                agent = RankBasedAgent(player_id)
            else:
                msg = f"Unknown opponent type: {opponent_type}"
                raise ValueError(msg)

            opponents.append(agent)

        return opponents

    def _is_learning_agent_active(self) -> bool:
        """Check if learning agent is active (hasn't banked this round)."""
        if self.game is None:
            return False
        player = self.game.state.get_player(self.learning_agent_id)
        return player is not None and not player.has_banked_this_round

    def _should_start_new_round(self) -> bool:
        """Check if we should start a new round."""
        if self.game is None or not self.game.is_round_over():
            return False
        if self.game.state.current_round is None:
            return True
        return self.game.state.current_round.round_number < self.total_rounds

    def _advance_game_to_next_decision(self) -> None:
        """Advance game state until learning agent needs to decide or game ends."""
        while not self.game.is_game_over():  # type: ignore[union-attr]
            if self._is_learning_agent_active():
                # Learning agent active - check if round is over
                if self._should_start_new_round():
                    self.game.start_new_round()  # type: ignore[union-attr]
                    break  # Learning agent can act in new round

                if self.game.is_round_over():  # type: ignore[union-attr]
                    break  # Game over check will trigger on next iteration

                # Roll dice and let opponents decide
                self.game.process_roll()  # type: ignore[union-attr]
                if self.game.is_round_over():  # type: ignore[union-attr]
                    continue  # Round ended by seven

                self.game.poll_decisions()  # type: ignore[union-attr]
                if self.game.is_round_over():  # type: ignore[union-attr]
                    continue  # All opponents banked

                break  # Learning agent's turn

            # Learning agent has banked - continue without them
            if self._should_start_new_round():
                self.game.start_new_round()  # type: ignore[union-attr]
                if self._is_learning_agent_active():
                    break  # Learning agent active in new round
                continue

            if self.game.is_round_over():  # type: ignore[union-attr]
                break  # Will check game over on next iteration

            # Continue round
            self.game.process_roll()  # type: ignore[union-attr]
            if not self.game.is_round_over():  # type: ignore[union-attr]
                self.game.poll_decisions()  # type: ignore[union-attr]

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Execute one step in the environment.

        Takes the learning agent's action, executes it in the game,
        and continues the game until the learning agent needs to act again
        or the game ends.

        Args:
            action: 0=pass, 1=bank

        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
            - observation: 14-dimensional state vector
            - reward: Placeholder 0.0 (Task 2.2 will implement rewards)
            - terminated: True if episode ended naturally (game over)
            - truncated: Always False (no time limits)
            - info: Dictionary with game state information

        Raises:
            RuntimeError: If called before reset() or after episode ends

        """
        if self.game is None:
            msg = "Must call reset() before step()"
            raise RuntimeError(msg)

        if self.game.is_game_over():
            msg = "Episode has ended, call reset() to start new episode"
            raise RuntimeError(msg)

        # Execute learning agent's action
        if action == 1:  # bank
            self.game.player_banks(self.learning_agent_id)
        # action == 0 is pass (do nothing)

        # Continue game until learning agent needs to act again or game ends
        self._advance_game_to_next_decision()

        # Get observation for next state
        obs = self.game.create_observation(self.learning_agent_id)
        flat_obs = flatten_observation(obs, self.total_rounds)

        # Check if episode terminated
        terminated = self.game.is_game_over()
        truncated = False  # No time limits

        # Calculate reward
        reward = self._calculate_reward(terminated)

        # Collect info
        info: dict[str, Any] = {
            "round_number": obs["round_number"],
            "player_score": obs["player_score"],
            "all_scores": obs["all_player_scores"].copy(),
        }

        if terminated:
            # Add terminal info
            winner = self.game.get_winner()
            if winner:
                info["winner_id"] = winner.player_id
                info["winner_score"] = winner.score
                info["did_win"] = winner.player_id == self.learning_agent_id
                info["player_rank"] = self._get_player_rank()

            # Add tournament info if applicable
            if self.reward_scheme == "tournament":
                info["tournament_game"] = self.current_tournament_game
                info["tournament_progress"] = len(self.tournament_results)
                if len(self.tournament_results) == self.tournament_size:
                    info["tournament_complete"] = True
                    info["tournament_reward"] = reward

        return flat_obs, reward, terminated, truncated, info

    def get_action_mask(self) -> np.ndarray:
        """Get mask for valid actions.

        Returns:
            Binary array where 1 = valid action, 0 = invalid
            Shape: (2,) corresponding to [pass, bank]

        """
        if self.game is None:
            return np.array([1, 1], dtype=np.int8)

        # Get current observation
        obs = self.game.create_observation(self.learning_agent_id)
        can_bank = obs["can_bank"]

        # Pass is always valid, bank only if can_bank is True
        return np.array([1, 1 if can_bank else 0], dtype=np.int8)

    def _get_player_rank(self) -> int:
        """Get the learning agent's rank (1=best, N=worst).

        Returns:
            Rank position (1-indexed)

        """
        if self.game is None:
            return 1

        # Get all final scores
        scores = [(p.player_id, p.score) for p in self.game.state.players]
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Find learning agent's rank
        for rank, (pid, _) in enumerate(scores, start=1):
            if pid == self.learning_agent_id:
                return rank

        return len(scores)  # Fallback

    def _calculate_reward(self, game_over: bool) -> float:
        """Calculate reward based on configured scheme.

        Args:
            game_over: Whether the game has ended

        Returns:
            Reward value

        """
        # No reward until game is over
        if not game_over:
            return 0.0

        if self.game is None:
            return 0.0

        # Sparse reward: simple win/loss
        if self.reward_scheme == "sparse":
            return self._calculate_sparse_reward()

        # Tournament reward: accumulate results, reward after N games
        if self.reward_scheme == "tournament":
            return self._calculate_tournament_reward()

        return 0.0

    def _calculate_sparse_reward(self) -> float:
        """Calculate sparse reward: +1 for win, -1 for loss, 0 for tie.

        Returns:
            Reward value

        """
        if self.game is None:
            return 0.0

        winner = self.game.get_winner()
        if winner is None:
            return 0.0  # Tie (rare but possible)

        if winner.player_id == self.learning_agent_id:
            return 1.0  # Win
        return -1.0  # Loss

    def _calculate_tournament_reward(self) -> float:
        """Calculate tournament-based reward.

        Accumulates game results over tournament_size games, then calculates
        reward based on win rate, average rank, and consistency.

        Returns:
            Reward value (0.0 until tournament completes, then aggregate reward)

        """
        if self.game is None:
            return 0.0

        # Record this game's result
        winner = self.game.get_winner()
        did_win = winner is not None and winner.player_id == self.learning_agent_id
        rank = self._get_player_rank()

        game_result = {
            "did_win": did_win,
            "rank": rank,
            "score": self.game.state.get_player(self.learning_agent_id).score
            if self.game.state.get_player(self.learning_agent_id)
            else 0,
        }

        self.tournament_results.append(game_result)
        self.current_tournament_game += 1

        # If tournament not complete, return 0
        if len(self.tournament_results) < self.tournament_size:
            return 0.0

        # Tournament complete - calculate aggregate reward
        wins = sum(1 for r in self.tournament_results if r["did_win"])
        win_rate = wins / len(self.tournament_results)
        avg_rank = float(np.mean([r["rank"] for r in self.tournament_results]))
        ranks = [r["rank"] for r in self.tournament_results]
        rank_std = float(np.std(ranks))

        # Normalize rank to [0, 1] where 1 is best
        # With N players: rank 1 → 1.0, rank N → 0.0
        num_players = len(self.game.state.players)
        normalized_rank = (num_players - avg_rank) / (num_players - 1) if num_players > 1 else 1.0

        # Consistency bonus: reward low variance in ranks
        consistency_bonus = (
            self.tournament_consistency_weight if rank_std < self.tournament_consistency_threshold else 0.0
        )

        # Compute weighted reward
        reward = (
            self.tournament_win_weight * win_rate + self.tournament_rank_weight * normalized_rank + consistency_bonus
        )

        # Reset tournament tracking
        self.tournament_results = []
        self.current_tournament_game = 0

        return reward

    def render(self, mode: str = "human") -> None:
        """Render the current game state.

        Args:
            mode: Rendering mode (only "human" supported)

        """
        if self.game is None:
            print("Game not initialized. Call reset() first.")
            return

        print("\n" + "=" * 60)
        print("BANK! Training Environment")
        print("=" * 60)

        if self.game.state.current_round:
            round_num = self.game.state.current_round.round_number
            print(f"Round: {round_num}/{self.total_rounds}")
            print(f"Roll Count: {self.game.state.current_round.roll_count}")
            print(f"Current Bank: {self.game.state.current_round.current_bank}")
            if self.game.state.current_round.last_roll:
                print(f"Last Roll: {self.game.state.current_round.last_roll}")

        print("\nPlayer Scores:")
        for player in self.game.state.players:
            marker = " (LEARNING)" if player.player_id == self.learning_agent_id else ""
            if self.game.agents[player.player_id]:
                agent_name = self.game.agents[player.player_id].name
            else:
                agent_name = "DQN"
            print(f"  {agent_name}{marker}: {player.score}")

        if self.game.is_game_over():
            winner = self.game.get_winner()
            if winner:
                print(f"\n🏆 Winner: Player {winner.player_id} with {winner.score} points!")

        print("=" * 60 + "\n")
