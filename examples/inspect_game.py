"""
Game State Inspection Example

This example shows how to inspect and analyze game state during play.
"""

from bank.game.engine import BankGame
from bank.agents.random_agent import RandomAgent


def analyze_game_state(game):
    """Print detailed analysis of current game state."""
    state = game.state
    
    print("\n" + "=" * 60)
    print("Game State Analysis")
    print("=" * 60)
    
    print(f"\nRound: {state.round_number}")
    print(f"Current Player: {state.current_player.name}")
    print(f"Deck Size: {len(state.deck)} cards")
    print(f"Discard Pile: {len(state.discard_pile)} cards")
    
    print("\nPlayer Details:")
    for player in state.players:
        print(f"\n  {player.name}:")
        print(f"    Hand: {sorted(player.hand)}")
        print(f"    Bank: {sorted(player.bank)}")
        print(f"    Score: {player.score}")
        
        # Calculate some statistics
        if player.hand:
            avg_hand = sum(player.hand) / len(player.hand)
            print(f"    Average hand value: {avg_hand:.1f}")
        
        if player.bank:
            avg_bank = sum(player.bank) / len(player.bank)
            print(f"    Average banked value: {avg_bank:.1f}")


def play_with_analysis(num_turns=10):
    """Play a game with periodic state analysis."""
    print("=" * 60)
    print("Game State Inspection Example")
    print("=" * 60)
    
    # Create game
    game = BankGame(num_players=2, player_names=["Alice", "Bob"])
    
    # Create agents
    agents = [
        RandomAgent(player_id=0, name="Alice", seed=42),
        RandomAgent(player_id=1, name="Bob", seed=43)
    ]
    
    # Play turns and analyze
    for turn in range(num_turns):
        if game.is_game_over():
            break
        
        current_agent = agents[game.state.current_player_idx]
        valid_actions = game.get_valid_actions()
        
        if not valid_actions:
            break
        
        # Select and perform action
        action, params = current_agent.select_action(game.state, valid_actions)
        print(f"\nTurn {turn + 1}: {current_agent.name} performs {action} {params}")
        game.take_action(action, **params)
        
        # Analyze state every 5 turns
        if (turn + 1) % 5 == 0:
            analyze_game_state(game)
    
    # Final analysis
    print("\n" + "=" * 60)
    print("FINAL STATE")
    analyze_game_state(game)
    
    if game.is_game_over():
        winner = game.get_winner()
        if winner:
            print(f"\n🏆 Winner: {winner.name} with {winner.score} points!")


def main():
    """Run the example."""
    play_with_analysis(num_turns=20)


if __name__ == "__main__":
    main()
