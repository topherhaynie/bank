# Reward Schemes for BANK! Training

This document describes the reward calculation schemes implemented in the BankEnv environment for reinforcement learning training.

## Overview

The environment supports two reward schemes that can be selected via the `reward_scheme` parameter:

1. **Sparse**: Simple win/loss rewards (+1/-1)
2. **Tournament**: Aggregate results over N games with win rate, rank, and consistency components

All reward parameters are configurable to support experimentation.

## Sparse Reward Scheme

### Description
The simplest baseline approach that provides clear gradient signals focused on winning.

### Reward Calculation
- **Win**: +1.0
- **Loss**: -1.0
- **Tie**: 0.0 (rare in BANK!)

### When to Use
- Initial training to establish baseline performance
- When you want clear, interpretable signals
- For debugging and validating the training pipeline
- When training instability occurs with more complex schemes

### Configuration
```python
env = BankEnv(
    num_opponents=3,
    opponent_types=["smart", "aggressive", "conservative"],
    reward_scheme="sparse"
)
```

### Pros
- Clear gradient signal: winning is good, losing is bad
- No delay in feedback (reward at end of every game)
- Simple to understand and debug
- Works well with high-variance games like BANK!

### Cons
- Binary signal may be too coarse for learning nuanced strategies
- Doesn't distinguish between close losses and blowouts
- No credit for good play that doesn't result in a win

## Tournament Reward Scheme

### Description
Accumulates results over N games (default 5) and provides a composite reward based on:
1. Win rate
2. Average rank across games
3. Consistency (low variance in ranks)

This scheme reduces variance and provides richer feedback about performance trends.

### Reward Calculation

After N games in a tournament, the reward is calculated as:

```
reward = win_weight × win_rate 
       + rank_weight × normalized_rank
       + consistency_bonus
```

Where:
- **win_rate**: Fraction of games won in tournament (0.0 to 1.0)
- **normalized_rank**: Average rank converted to [0, 1] scale where 1.0 is best
  - Formula: `(num_players - avg_rank) / (num_players - 1)`
  - Example with 4 players: rank 1 → 1.0, rank 2 → 0.67, rank 3 → 0.33, rank 4 → 0.0
- **consistency_bonus**: Awarded if rank standard deviation < threshold
  - Reward for stable performance across games

### Default Parameters

```python
tournament_size = 5                        # Games per tournament
tournament_win_weight = 2.0                # Weight for win rate (0-100%)
tournament_rank_weight = 1.0               # Weight for rank component
tournament_consistency_weight = 0.5        # Bonus for consistent ranks
tournament_consistency_threshold = 0.5     # Std dev threshold for bonus
```

### Configuration Example

```python
env = BankEnv(
    num_opponents=3,
    opponent_types=["smart", "aggressive", "conservative"],
    reward_scheme="tournament",
    tournament_size=5,
    tournament_win_weight=2.0,
    tournament_rank_weight=1.0,
    tournament_consistency_weight=0.5,
    tournament_consistency_threshold=0.5,
)
```

### Reward Range

With default weights:
- **Best case**: 3.5 (5/5 wins, all rank 1, consistent) = 2.0 + 1.0 + 0.5
- **Worst case**: 0.0 (0/5 wins, all rank N, inconsistent) = 0.0 + 0.0 + 0.0
- **Typical range**: 1.0 to 3.0

### Example Tournament Results

From test run (4 players, 5 games):
- **Tournament 1**: 4 wins, 1 loss (rank 2) → Reward: 3.033
  - Win rate: 0.8 × 2.0 = 1.6
  - Avg rank 1.2 → normalized 0.933 × 1.0 = 0.933
  - Consistent → +0.5
  
- **Tournament 2**: 2 wins, 3 losses (ranks 2,1,1,2,3) → Reward: 1.533
  - Win rate: 0.4 × 2.0 = 0.8
  - Avg rank 1.8 → normalized 0.733 × 1.0 = 0.733
  - Not consistent → +0.0

### When to Use
- After initial training establishes basic competence
- When you want to reduce variance in gradient signals
- For final optimization and fine-tuning
- When experimenting with different opponent mixes

### Pros
- Reduces variance by averaging over multiple games
- Rewards consistent performance, not just lucky wins
- Provides richer feedback about relative performance
- Can help escape local optima (rank info even when not winning)

### Cons
- Delayed feedback (only every N games)
- More complex to tune (multiple hyperparameters)
- May slow initial learning compared to sparse

## Hyperparameter Tuning Guidance

### Tournament Size
- **Smaller (3-5)**: Faster feedback, more variance
- **Larger (10-20)**: More stable gradients, slower learning
- **Recommendation**: Start with 5, increase if training is unstable

### Win Weight
- **Higher (2.0-3.0)**: Emphasize winning over placement
- **Lower (0.5-1.0)**: More weight on consistent performance
- **Recommendation**: Start with 2.0 (matches documented design)

### Rank Weight
- **Higher (1.0-2.0)**: Encourage strong finishes even without wins
- **Lower (0.2-0.5)**: Focus primarily on wins
- **Recommendation**: Start with 1.0 (balanced)

### Consistency Weight & Threshold
- **Weight**: Bonus magnitude for consistent performance (0.3-0.8)
- **Threshold**: Std dev cutoff for bonus (0.3-0.7)
- **Recommendation**: 0.5 and 0.5 (moderate expectations)

## Implementation Details

### Info Dictionary

The `step()` method returns an info dictionary with reward-related metadata:

#### All Schemes
```python
info = {
    "round_number": int,        # Current round
    "player_score": int,        # Learning agent's score
    "all_scores": dict,         # All player scores
    "winner_id": int,           # Winner's player ID (if game over)
    "winner_score": int,        # Winner's score (if game over)
    "did_win": bool,            # Whether learning agent won (if game over)
    "player_rank": int,         # Learning agent's rank (if game over)
}
```

#### Tournament Scheme Additional Fields
```python
info.update({
    "tournament_game": int,           # Current game in tournament (1-N)
    "tournament_progress": int,       # Games completed so far
    "tournament_complete": bool,      # True when reward is given
    "tournament_reward": float,       # The aggregate reward (if complete)
})
```

### State Management

Tournament state is maintained within the environment:
- `tournament_results`: List of game results (win, rank, score)
- `current_tournament_game`: Counter for current tournament

State resets when a tournament completes (reward given) or when `reset(seed=...)` is called with a new seed.

## Excluded Schemes

Based on user priorities (focus on winning, avoid gaming round-level rewards), the following schemes from the original design doc were **not implemented**:

### Dense (Step-by-Step) Rewards
- **Why excluded**: Risk of encouraging early banking for easy rewards instead of playing to win
- **Concern**: Agent might optimize for frequent small banks rather than optimal scoring strategy

### Score-Differential Rewards  
- **Why excluded**: Focus on winning, not score gaps
- **Alternative**: Tournament scheme's rank component provides similar information

These schemes could be added later if needed for experimentation.

## Testing

The reward schemes have been validated with:
- Sparse: 10 games showing correct ±1 rewards
- Tournament: 15 games (3 tournaments) with proper aggregation
- Configuration: All parameters tested as configurable

See test results in git history (`test_rewards.py`).

## Usage in Training

### Training Loop Example

```python
from bank.training.environment import BankEnv

# Create environment with desired reward scheme
env = BankEnv(
    num_opponents=3,
    opponent_types=["smart", "aggressive", "conservative"],
    reward_scheme="tournament",  # or "sparse"
    tournament_size=5,
)

# Training loop
for episode in range(num_episodes):
    obs, info = env.reset(seed=episode)
    episode_reward = 0.0
    
    while True:
        action = agent.act(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        
        # Note: reward is 0 until game ends (sparse) or tournament completes
        if reward != 0.0:
            agent.update(reward)
            episode_reward += reward
            
        if terminated:
            break
    
    # Log tournament progress if applicable
    if env.reward_scheme == "tournament":
        print(f"Tournament progress: {info.get('tournament_progress', 0)}/{env.tournament_size}")
```

## Next Steps

When implementing the DQN agent (Task 3):
1. Handle delayed rewards properly (tournament scheme)
2. Use info dict to track tournament progress
3. Log reward components separately for analysis
4. Consider using replay buffer across tournament boundaries
5. Add TensorBoard logging for reward trends

## References

- Original design: `docs/PHASE4_ARCHITECTURE.md` lines 97-247
- Environment implementation: `bank/training/environment.py`
- Test validation: Git history (`test_rewards.py`)
