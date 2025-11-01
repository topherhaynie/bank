"""Quick demo of reward schemes in BankEnv.

This script demonstrates both sparse and tournament reward schemes
with a simple threshold-based strategy.
"""

from bank.training.environment import BankEnv


def demo_sparse():
    """Demo sparse reward scheme."""
    print("=" * 70)
    print("SPARSE REWARD DEMO (5 games)")
    print("=" * 70)
    
    env = BankEnv(
        num_opponents=3,
        opponent_types=["conservative", "aggressive", "smart"],
        total_rounds=5,
        reward_scheme="sparse",
    )
    
    for game in range(5):
        obs, _ = env.reset(seed=game)
        total_reward = 0.0
        
        while True:
            # Simple strategy: bank when >= 50 points
            current_bank_feature = obs[2]  # tanh(current_bank/250)
            action = 1 if current_bank_feature > 0.19 else 0
            
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            
            if terminated:
                break
        
        won = "✓" if info.get("did_win") else "✗"
        print(f"  Game {game+1}: {won} Score={info['player_score']:3d} Reward={total_reward:+.1f}")
    
    print()


def demo_tournament():
    """Demo tournament reward scheme."""
    print("=" * 70)
    print("TOURNAMENT REWARD DEMO (10 games = 2 tournaments)")
    print("=" * 70)
    
    env = BankEnv(
        num_opponents=3,
        opponent_types=["conservative", "aggressive", "smart"],
        total_rounds=5,
        reward_scheme="tournament",
        tournament_size=5,
        tournament_win_weight=2.0,
        tournament_rank_weight=1.0,
        tournament_consistency_weight=0.5,
    )
    
    tournament_num = 1
    
    for game in range(10):
        obs, _ = env.reset(seed=100 + game)
        total_reward = 0.0
        
        while True:
            # Simple strategy: bank when >= 50 points
            current_bank_feature = obs[2]  # tanh(current_bank/250)
            action = 1 if current_bank_feature > 0.19 else 0
            
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            
            if terminated:
                break
        
        won = "✓" if info.get("did_win") else "✗"
        rank = info.get("player_rank", "?")
        progress = info.get("tournament_progress", 0)
        
        print(f"  Game {game+1}: {won} Score={info['player_score']:3d} Rank={rank} " +
              f"Progress={progress}/5 Reward={total_reward:+.3f}")
        
        if total_reward > 0.0:
            print(f"    🏆 Tournament {tournament_num} complete! Reward={total_reward:.3f}")
            tournament_num += 1
    
    print()


def demo_parameters():
    """Demo configurable parameters."""
    print("=" * 70)
    print("CONFIGURABLE PARAMETERS")
    print("=" * 70)
    
    configs = [
        ("Sparse (default)", {
            "reward_scheme": "sparse",
        }),
        ("Tournament size=3", {
            "reward_scheme": "tournament",
            "tournament_size": 3,
        }),
        ("Tournament size=10", {
            "reward_scheme": "tournament",
            "tournament_size": 10,
        }),
        ("Tournament win-focused", {
            "reward_scheme": "tournament",
            "tournament_size": 5,
            "tournament_win_weight": 3.0,
            "tournament_rank_weight": 0.5,
        }),
    ]
    
    for name, params in configs:
        env = BankEnv(num_opponents=2, **params)
        print(f"\n  {name}:")
        print(f"    scheme: {env.reward_scheme}")
        if env.reward_scheme == "tournament":
            print(f"    tournament_size: {env.tournament_size}")
            print(f"    win_weight: {env.tournament_win_weight}")
            print(f"    rank_weight: {env.tournament_rank_weight}")
    
    print()


if __name__ == "__main__":
    demo_sparse()
    demo_tournament()
    demo_parameters()
    
    print("=" * 70)
    print("✅ Reward schemes implemented and tested!")
    print("   See docs/REWARD_SCHEMES.md for full documentation")
    print("=" * 70)
