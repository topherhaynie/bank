"""
Simple Agent Example

This example shows how to create a custom agent and run a game.
"""

from bank.game.engine import BankGame
from bank.agents.base import BaseAgent
from bank.agents.random_agent import RandomAgent
from bank.cli.game_runner import GameRunner


class GreedyAgent(BaseAgent):
    """
    A simple greedy agent that always tries to maximize immediate score.
    
    Strategy:
    - Bank the highest value card when possible
    - Draw cards if hand is small
    - Play lowest value card as last resort
    """
    
    def select_action(self, game_state, valid_actions):
        """Select action based on greedy strategy."""
        player = game_state.players[self.player_id]
        
        # Strategy 1: Bank highest value card if we can
        if "bank_card" in valid_actions and player.hand:
            # Find the highest value card
            best_idx = max(range(len(player.hand)), key=lambda i: player.hand[i])
            return ("bank_card", {"card_idx": best_idx})
        
        # Strategy 2: Draw cards if hand is getting low
        if "draw_card" in valid_actions and len(player.hand) < 3:
            return ("draw_card", {})
        
        # Strategy 3: Play lowest value card to keep good cards
        if "play_card" in valid_actions and player.hand:
            worst_idx = min(range(len(player.hand)), key=lambda i: player.hand[i])
            return ("play_card", {"card_idx": worst_idx})
        
        # Fallback: first valid action
        if valid_actions:
            return (valid_actions[0], {})
        
        return ("pass", {})


def main():
    """Run a game with custom agents."""
    print("=" * 60)
    print("Simple Agent Example - GreedyAgent vs RandomAgent")
    print("=" * 60)
    print()
    
    # Create a game with 2 players
    player_names = ["GreedyBot", "RandomBot"]
    game = BankGame(num_players=2, player_names=player_names)
    
    # Create agents
    agents = [
        GreedyAgent(player_id=0, name="GreedyBot"),
        RandomAgent(player_id=1, name="RandomBot", seed=42)
    ]
    
    # Run the game
    runner = GameRunner(game, agents, delay=0.3)
    runner.run()
    
    print("\nGame complete!")


if __name__ == "__main__":
    main()
