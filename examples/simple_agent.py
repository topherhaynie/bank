"""Simple Agent Example.

This example shows how to create a custom agent for the BANK! dice game.
Demonstrates the Agent interface and how to make strategic decisions.
"""

from bank.agents.base import Action, Agent, Observation
from bank.agents.random_agent import RandomAgent
from bank.cli.game_runner import GameRunner
from bank.game.engine import BankGame


class CautiousAgent(Agent):
    """A cautious agent that banks when the bank reaches a safe threshold.

    Strategy:
    - Bank immediately if bank value >= threshold
    - After roll 3, become more cautious (lower threshold)
    - If leading, play more conservatively
    - If trailing, take more risks

    This demonstrates:
    - Accessing observation fields
    - Making bank/pass decisions
    - Adjusting strategy based on game state
    """

    def __init__(
        self,
        player_id: int,
        name: str | None = None,
        base_threshold: int = 50,
    ) -> None:
        """Initialize the cautious agent.

        Args:
            player_id: Unique identifier for this player
            name: Optional name for the agent
            base_threshold: Base bank value to aim for before banking

        """
        super().__init__(player_id, name or f"CautiousBot-{player_id}")
        self.base_threshold = base_threshold

    def act(self, observation: Observation) -> Action:
        """Make a banking decision based on cautious strategy.

        Args:
            observation: Current game state information

        Returns:
            Either "bank" or "pass"

        """
        # Can't bank if already banked
        if not observation["can_bank"]:
            return "pass"

        current_bank = observation["current_bank"]
        roll_count = observation["roll_count"]
        my_score = observation["player_score"]

        # Calculate dynamic threshold based on game state
        threshold = self.base_threshold

        # After roll 3, danger of seven increases - lower threshold
        if roll_count > 3:  # noqa: PLR2004
            threshold = int(threshold * 0.7)  # 30% more cautious

        # Check if we're leading or trailing
        max_opponent_score = max(
            score for pid, score in observation["all_player_scores"].items() if pid != observation["player_id"]
        )

        if my_score > max_opponent_score:
            # Leading: play more conservatively
            threshold = int(threshold * 0.8)  # 20% more cautious
        elif my_score < max_opponent_score - 50:
            # Trailing significantly: take more risks
            threshold = int(threshold * 1.3)  # 30% more aggressive

        # Bank if we've reached our threshold
        if current_bank >= threshold:
            return "bank"

        return "pass"

    def reset(self) -> None:
        """Reset agent state for a new game."""
        # This agent is stateless, so no reset needed


class AlwaysBankAt100(Agent):
    """Simple agent that always banks when bank reaches 100 points.

    This is the simplest possible agent - demonstrates minimal implementation.
    """

    def act(self, observation: Observation) -> Action:
        """Bank at 100 points, otherwise pass."""
        if observation["can_bank"] and observation["current_bank"] >= 100:  # noqa: PLR2004
            return "bank"
        return "pass"


def main() -> None:
    """Run a game comparing custom agents."""
    print("=" * 60)
    print("Simple Agent Example - Custom Agents vs Random")
    print("=" * 60)
    print()
    print("Demonstrating three agent strategies:")
    print("  1. CautiousAgent - Adaptive threshold-based banking")
    print("  2. AlwaysBankAt100 - Simple fixed threshold")
    print("  3. RandomAgent - Random decisions for comparison")
    print()

    # Create a game with 3 players
    player_names = ["CautiousBot", "SimpleBot", "RandomBot"]
    game = BankGame(
        num_players=3,
        player_names=player_names,
        total_rounds=5,
        rng=None,  # Use random seed
    )

    # Create agents with different strategies
    agents = [
        CautiousAgent(player_id=0, name="CautiousBot", base_threshold=60),
        AlwaysBankAt100(player_id=1, name="SimpleBot"),
        RandomAgent(player_id=2, name="RandomBot", seed=42),
    ]

    # Assign agents to the game
    game.agents = agents

    # Run the game
    runner = GameRunner(game, agents, delay=0.3, verbose=True)
    final_scores = runner.run()

    print("\n" + "=" * 60)
    print("Analysis")
    print("=" * 60)
    print("\nFinal Scores:")
    for player_id, score in sorted(final_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {player_names[player_id]}: {score} points")

    print("\nKey Takeaways:")
    print("  - CautiousAgent adapts threshold based on game state")
    print("  - SimpleBot uses fixed threshold (easy to understand)")
    print("  - RandomAgent provides baseline comparison")
    print("  - Custom agents implement act(observation) -> Action")
    print()


if __name__ == "__main__":
    main()
