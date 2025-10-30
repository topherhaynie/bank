# Phase 4: Training Environment & DQN Architecture

## Overview

This document outlines the architectural design for Phase 4, focusing on creating a flexible, well-architected training system that allows easy experimentation with reward schemes, observation encodings, and training hyperparameters.

## Current Status

The training module (`bank/training/`) exists with skeleton code from the legacy card game. It needs to be completely redesigned for the dice game with a focus on:

1. **Flexibility**: Easy to adjust rewards, observations, and training parameters
2. **Modularity**: Clean separation between environment, agent, and training loop
3. **Observability**: Comprehensive logging and checkpointing
4. **Reproducibility**: Deterministic seeding and experiment tracking

## Core Components

### 1. Environment Wrapper (`bank/training/environment.py`)

**Purpose**: Bridge between the game engine and RL algorithms.

**Key Design Decisions**:

#### A. Observation Space Design

**Source**: The game engine already provides a structured `Observation` TypedDict (defined in `bank/agents/base.py`) with 9 fields:
- `round_number`, `roll_count`, `current_bank`, `last_roll`
- `active_player_ids`, `player_id`, `player_score`, `can_bank`
- `all_player_scores` (dict of all player scores)

**Flattening Strategy**: Convert the TypedDict to a flat numpy array for neural network input.

**Proposed Flat Vector Encoding** (14 features):
```python
def flatten_observation(obs: Observation, total_rounds: int = 10) -> np.ndarray:
    """Convert Observation TypedDict to flat numpy array."""
    
    # Extract opponent scores
    opponent_scores = [
        score for pid, score in obs["all_player_scores"].items() 
        if pid != obs["player_id"]
    ]
    max_opponent = max(opponent_scores) if opponent_scores else 0
    min_opponent = min(opponent_scores) if opponent_scores else 0
    avg_opponent = sum(opponent_scores) / len(opponent_scores) if opponent_scores else 0
    
    # Compute derived features
    is_first_three = obs["roll_count"] <= 3
    is_leading = obs["player_score"] >= max_opponent
    score_gap = obs["player_score"] - max_opponent
    
    # Build flat vector (all normalized to [0, 1] range)
    features = [
        obs["round_number"] / total_rounds,        # [0, 1]
        obs["roll_count"] / 10.0,                  # [0, ~1]
        obs["current_bank"] / 500.0,               # [0, ~1]
        obs["last_roll"][0] / 6.0 if obs["last_roll"] else 0,  # [0, 1]
        obs["last_roll"][1] / 6.0 if obs["last_roll"] else 0,  # [0, 1]
        float(is_first_three),                     # {0, 1}
        obs["player_score"] / 1000.0,              # [0, ~1]
        float(obs["can_bank"]),                    # {0, 1}
        len(obs["active_player_ids"]) / 4.0,       # [0, 1] assuming max 4 players
        avg_opponent / 1000.0,                     # [0, ~1]
        max_opponent / 1000.0,                     # [0, ~1]
        min_opponent / 1000.0,                     # [0, ~1]
        float(is_leading),                         # {0, 1}
        (score_gap + 500) / 1000.0,                # [0, ~1] centered
    ]
    
    return np.array(features, dtype=np.float32)
```

**Design Notes**:
- Reuses existing `Observation` TypedDict (no changes to game engine needed)
- All features normalized to roughly [0, 1] range for stable neural network training
- Includes competitive features (opponent scores, leadership, gaps)
- Total: 14 features → input to neural network

#### B. Action Space

```python
action_space = spaces.Discrete(2)
# 0 = pass (continue rolling)
# 1 = bank (secure points)
```

**Action Masking**: Critical for valid actions
```python
if not can_bank:
    # Mask action 1 (bank) as invalid
    # Agent must choose action 0 (pass)
    action_mask = [1, 0]  # Only pass is valid
else:
    action_mask = [1, 1]  # Both actions valid
```

#### C. Reward Design (Highly Configurable)

**Critical Design Consideration**: BANK! has high variance in game outcomes. Some games produce scores of 500+, others end with scores under 100. This variance makes step-by-step reward shaping challenging, as the "correct" strategy depends heavily on game dynamics.

**Proposed Reward Schemes**:

**Scheme 1: Tournament-Based (Recommended for Stability)**
```python
# Accumulate per-game results over N games, then assign reward
# This smooths variance and focuses on consistent winning

tournament_size = 5  # Every 5 games, calculate reward

# Track results over tournament
tournament_results = []  # [(rank, score, opponent_types), ...]

# After tournament_size games:
avg_rank = sum(r[0] for r in tournament_results) / tournament_size
win_rate = sum(1 for r in tournament_results if r[0] == 1) / tournament_size
avg_score = sum(r[1] for r in tournament_results) / tournament_size

# Reward based on tournament performance
reward = {
    "win_rate_component": win_rate * 2.0,           # +2 if won all games
    "rank_component": (4 - avg_rank) / 3.0,         # +1 if avg rank 1, -1 if avg rank 4
    "consistency_bonus": 0.5 if std_dev(ranks) < 0.5 else 0,
}
total_reward = sum(reward.values())

# Assign this reward to all transitions from that tournament
# This encourages strategies that win consistently, not just occasionally
```

**Scheme 2: Sparse Rewards (Simplest baseline)**
```python
# Only reward at game end based on outcome
reward = {
    "game_end": +1 if won else -1 if lost else 0,
    "during_game": 0,
}
```

**Scheme 3: Dense Rewards (Direct feedback)**
```python
# Immediate feedback for actions
reward = {
    "bank": +amount_banked / 100,           # Positive for banking
    "seven_rolled": -current_bank / 100,    # Negative for losing bank
    "round_end_unbanked": -bank_value / 100,# Penalty for not banking
    "game_end": +1 if won else -1,          # Final outcome bonus
}
```

**Scheme 4: Outcome + Score Differential**
```python
# Reward based on final score gap (works for 4-player games)
final_score_gap = my_score - max_opponent_score

reward = {
    "win": +5.0 if rank == 1 else 0,
    "score_gap": final_score_gap / 200,     # Scaled gap
    "above_average": +1.0 if my_score > avg_score else -0.5,
}
```

**Configuration System**:
```python
reward_config = {
    "scheme": "tournament",  # "tournament", "sparse", "dense", "score_differential"
    
    # Tournament scheme settings
    "tournament_size": 5,
    "win_rate_weight": 2.0,
    "rank_weight": 1.0,
    "consistency_bonus": 0.5,
    
    # Dense scheme settings
    "bank_reward_scale": 0.01,
    "seven_penalty_scale": 0.02,
    
    # General settings
    "normalize": True,
    "clip_range": [-5, 5],
}
```

### **Recommended Starting Point**

Based on your feedback and the architecture review:

**Task 1: Advanced Opponents First** ⭐
- Implement 4 advanced agents: LeaderOnly, LeaderPlusOne, Leech, RankBased
- These are critical for training a robust DQN agent
- Estimated time: 0.5-1 day

**Task 2: Environment with Tournament Rewards**
- **Observation**: 14-feature flat vector from existing `Observation` TypedDict
- **Reward**: Tournament-based (5 games) with configurable formula
- **Action masking**: Prevent invalid banks
- Estimated time: 1-2 days

**Task 3: DQN Agent with Full Checkpointing**
- **Network**: Simple MLP (128→128→2)
- **Buffer**: 100K transitions with save/load
- **Checkpoints**: Full state (network, optimizer, epsilon, buffer, stats)
- **Agent protocol**: Compatible with game engine
- Estimated time: 2-3 days

**Task 4: Training Script with Interruption Handling**
- **Tournament grouping**: Assign rewards every 5 games
- **Interruption**: Graceful Ctrl+C handling with auto-save
- **Resume**: Full state restoration from checkpoints
- **Opponents**: Mixed training with 40% advanced agents
- **Logging**: TensorBoard for visualization
- Estimated time: 2-3 days

**First Training Run**:
```bash
# Start training
python -m bank.training.train --config configs/dqn_tournament_v1.json

# Training runs, you press Ctrl+C after 2000 episodes
# >> Interrupted! Saving checkpoint...
# >> Checkpoint saved: checkpoints/interrupted_2000.pth

# Resume later
python -m bank.training.train --config configs/dqn_tournament_v1.json --resume checkpoints/interrupted_2000.pth

# Train to completion (10,000 episodes)
# Evaluate: Does agent achieve >40% win rate vs SmartAgent?
```

**Experimentation After Baseline**:
Once you have a working baseline, you can easily experiment:
- Adjust tournament size (3, 5, 10, 20 games)
- Try different reward formulas (more rank-focused, more win-focused)
- Change opponent mix (more advanced agents, less basic agents)
- Tune network architecture (add layers, try dueling DQN)
- Adjust hyperparameters (learning rate, epsilon decay, batch size)

**Philosophy**: 
- ✅ **Flexible by design** - All key parameters in config files
- ✅ **Resume anytime** - Never lose training progress
- ✅ **Easy experimentation** - Change config, resume from checkpoint
- ✅ **Robust evaluation** - Test against hardest opponents

This gives you a working baseline quickly (~4-6 days), then you can iterate rapidly on reward schemes and training strategies.

**Ready to start?** Shall we begin with Task 1 (implementing the advanced opponent agents)?

#### D. Episode Termination

```python
terminated = game.state.game_over
truncated = False  # No time limits in this game

info = {
    "winner_id": game.state.winner,
    "final_scores": {p.player_id: p.score for p in game.state.players},
    "num_rounds": game.state.total_rounds,
    "agent_rank": agent_final_rank,
}
```

### 2. DQN Agent (`bank/training/dqn_agent.py`)

**Purpose**: Deep Q-Network agent compatible with both training and gameplay.

**Key Components**:

#### A. Network Architecture (Configurable)

```python
network_config = {
    "architecture": "mlp",  # Options: "mlp", "dueling", "noisy"
    "hidden_dims": [128, 128],
    "activation": "relu",
    "dropout": 0.0,
}
```

**Basic MLP**:
```python
Input (14 dims) -> Dense(128) -> ReLU -> Dense(128) -> ReLU -> Output(2 actions)
```

**Dueling Architecture** (Better for value estimation):
```python
Input -> Shared(128) -> Split:
    -> Value Stream -> V(s)
    -> Advantage Stream -> A(s,a)
Q(s,a) = V(s) + (A(s,a) - mean(A(s,:)))
```

#### B. Replay Buffer

```python
replay_buffer_config = {
    "capacity": 100_000,
    "batch_size": 64,
    "prioritized": False,  # Option for Prioritized Experience Replay
}
```

#### C. Training Hyperparameters

```python
training_config = {
    "gamma": 0.99,               # Discount factor
    "epsilon_start": 1.0,        # Exploration rate start
    "epsilon_end": 0.05,         # Exploration rate end
    "epsilon_decay": 0.995,      # Decay per episode
    "learning_rate": 1e-3,
    "target_update_freq": 100,   # Episodes between target network updates
    "train_freq": 4,             # Steps between gradient updates
    "gradient_clip": 1.0,        # Gradient clipping
}
```

#### D. Agent Interface Compatibility

**Critical**: DQN agent must implement the same `Agent` protocol:

```python
class DQNAgent(Agent):
    def __init__(self, player_id: int, name: str, model_path: str = None):
        self.player_id = player_id
        self.name = name
        self.network = DQNetwork(...)
        if model_path:
            self.load(model_path)
    
    def act(self, observation: Observation) -> Action:
        """Compatible with game engine's Agent interface."""
        # Convert Observation to tensor
        state = self._observation_to_tensor(observation)
        
        # Epsilon-greedy during training
        if self.training and random.random() < self.epsilon:
            action = random.choice(["bank", "pass"])
        else:
            q_values = self.network(state)
            action_idx = q_values.argmax().item()
            action = "bank" if action_idx == 1 else "pass"
        
        # Respect action mask
        if action == "bank" and not observation["can_bank"]:
            action = "pass"
        
        return action
    
    def reset(self) -> None:
        """Called at start of new game."""
        pass
```

### 3. Training Script (`bank/training/train.py`)

**Purpose**: Orchestrate training loop with logging, checkpointing, and evaluation.

**Critical Requirements**:
- **Interruptible**: Training can be stopped at any time (Ctrl+C)
- **Resumable**: Training can restart from last checkpoint
- **Stateful**: All state (network, optimizer, replay buffer, episode count, epsilon) saved

**Key Features**:

#### A. Training Loop Structure (Interruptible & Resumable)

```python
def train(config_path: str, resume_from: str = None):
    """Main training loop with interruption handling."""
    
    # 1. Load or initialize training state
    if resume_from:
        checkpoint = load_checkpoint(resume_from)
        agent = checkpoint["agent"]
        optimizer = checkpoint["optimizer"]
        start_episode = checkpoint["episode"]
        replay_buffer = checkpoint["replay_buffer"]
        training_stats = checkpoint["stats"]
        print(f"Resuming from episode {start_episode}")
    else:
        agent = DQNAgent(...)
        optimizer = create_optimizer(agent)
        start_episode = 0
        replay_buffer = ReplayBuffer(...)
        training_stats = {"rewards": [], "losses": [], "win_rates": []}
    
    # 2. Setup signal handler for graceful interruption
    def signal_handler(sig, frame):
        print("\nInterrupted! Saving checkpoint...")
        save_checkpoint({
            "agent": agent,
            "optimizer": optimizer,
            "episode": episode,
            "replay_buffer": replay_buffer,
            "stats": training_stats,
            "config": config,
        }, path=f"checkpoints/interrupted_{episode}.pth")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # 3. Training loop
    try:
        for episode in range(start_episode, num_episodes):
            # Tournament-based training (every N games)
            if episode % config["tournament_size"] == 0:
                tournament_results = []
            
            # Play episode
            obs, info = env.reset(seed=config["seed"] + episode)
            episode_reward = 0
            episode_transitions = []
            
            while not done:
                action = agent.act(obs)
                next_obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                
                # Store transition temporarily
                episode_transitions.append((obs, action, reward, next_obs, done))
                
                obs = next_obs
                episode_reward += reward
            
            # Store tournament result
            tournament_results.append({
                "rank": info["agent_rank"],
                "score": info["final_scores"][agent.player_id],
                "transitions": episode_transitions,
            })
            
            # 4. Tournament-based reward assignment
            if episode % config["tournament_size"] == config["tournament_size"] - 1:
                # Calculate tournament reward
                tournament_reward = calculate_tournament_reward(tournament_results, config)
                
                # Assign reward to all transitions in tournament
                for game in tournament_results:
                    for transition in game["transitions"]:
                        obs, action, _, next_obs, done = transition
                        replay_buffer.add(obs, action, tournament_reward, next_obs, done)
            
            # 5. Train agent
            if len(replay_buffer) > config["batch_size"]:
                loss = agent.train_step(replay_buffer, config["batch_size"])
                training_stats["losses"].append(loss)
            
            # 6. Decay exploration
            agent.decay_epsilon()
            
            # 7. Update target network
            if episode % config["target_update_freq"] == 0:
                agent.update_target_network()
            
            # 8. Logging
            if episode % config["log_freq"] == 0:
                logger.log({
                    "episode": episode,
                    "reward": episode_reward,
                    "epsilon": agent.epsilon,
                    "buffer_size": len(replay_buffer),
                })
            
            # 9. Evaluation
            if episode % config["eval_freq"] == 0:
                eval_results = evaluate_agent(agent, num_games=100, config=config)
                training_stats["win_rates"].append(eval_results["win_rate"])
                logger.log({"eval": eval_results})
            
            # 10. Checkpointing (automatic save)
            if episode % config["checkpoint_freq"] == 0:
                save_checkpoint({
                    "agent": agent,
                    "optimizer": optimizer,
                    "episode": episode,
                    "replay_buffer": replay_buffer,
                    "stats": training_stats,
                    "config": config,
                }, path=f"checkpoints/episode_{episode}.pth")
    
    except Exception as e:
        # Save on any error
        print(f"Error during training: {e}")
        save_checkpoint({...}, path=f"checkpoints/error_{episode}.pth")
        raise
    
    # 11. Final save
    save_checkpoint({...}, path="checkpoints/final.pth")
    print(f"Training complete! Final checkpoint saved.")
```

**Checkpoint Structure**:
```python
checkpoint = {
    "episode": int,                    # Current episode number
    "agent": {
        "network_state": state_dict,   # Neural network weights
        "target_network_state": state_dict,  # Target network weights
        "epsilon": float,              # Current exploration rate
        "config": dict,                # Agent hyperparameters
    },
    "optimizer": {
        "state_dict": state_dict,      # Optimizer state (momentum, etc.)
    },
    "replay_buffer": {
        "states": array,               # All stored states
        "actions": array,              # All stored actions
        "rewards": array,              # All stored rewards
        "next_states": array,          # All stored next states
        "dones": array,                # All stored done flags
        "position": int,               # Current buffer position
    },
    "training_stats": {
        "rewards": list,               # Episode rewards history
        "losses": list,                # Training losses history
        "win_rates": list,             # Evaluation win rates history
    },
    "config": dict,                    # Full training configuration
    "timestamp": str,                  # When checkpoint was saved
    "git_commit": str,                 # Code version (optional)
}
```

**Resume Command**:
```bash
# Start fresh training
python -m bank.training.train --config configs/dqn_tournament.json

# Resume from checkpoint
python -m bank.training.train --config configs/dqn_tournament.json --resume checkpoints/episode_5000.pth

# Resume from interrupted training (auto-finds latest)
python -m bank.training.train --config configs/dqn_tournament.json --resume-latest
```

#### B. Opponent Configuration

**Critical for learning**: Agent needs diverse and challenging opponents to develop robust strategies.

**Current Rule-Based Agents** (Phase 2, already implemented):
- `RandomAgent` - Random decisions (baseline)
- `ThresholdAgent` - Banks at fixed threshold
- `ConservativeAgent` - Banks early, low risk
- `AggressiveAgent` - Waits for high values
- `SmartAgent` - Adaptive based on context
- `AdaptiveAgent` - Adjusts based on competitive position

**Advanced Opponent Strategies** (Needed for Phase 4):

These strategies are particularly challenging and will push the DQN agent to learn sophisticated play:

**1. LeaderOnlyAgent** (Very Hard)
```python
"""Only banks if banking would make you the new leader."""
def act(self, obs):
    my_score_after = obs["player_score"] + obs["current_bank"]
    max_opponent = max(s for pid, s in obs["all_player_scores"].items() if pid != obs["player_id"])
    
    if obs["can_bank"] and my_score_after > max_opponent:
        return "bank"
    return "pass"
```
- **Strength**: Maximally aggressive, only cares about being #1
- **Weakness**: Can lose everything waiting for leadership

**2. LeaderPlusOneAgent** (Very Hard)
```python
"""Banks if becoming leader, but waits 1 extra roll for value."""
def act(self, obs):
    my_score_after = obs["player_score"] + obs["current_bank"]
    max_opponent = max(s for pid, s in obs["all_player_scores"].items() if pid != obs["player_id"])
    
    # Would become leader AND waited at least 1 roll after being able to bank
    if obs["can_bank"] and my_score_after > max_opponent and obs["roll_count"] >= 2:
        return "bank"
    return "pass"
```
- **Strength**: More balanced than LeaderOnly, gets better value
- **Weakness**: Still very risky

**3. LeechAgent** (Very Hard - "Shadow Strategy")
```python
"""Watches when others bank and waits 1 more roll for extra value."""
def act(self, obs):
    # Track who has banked this round
    num_banked = len([pid for pid in obs["all_player_scores"].keys() 
                      if pid not in obs["active_player_ids"]])
    
    # If most players have banked and we've waited 1+ rolls
    if obs["can_bank"] and num_banked >= 2 and obs["current_bank"] >= 40:
        return "bank"
    return "pass"
```
- **Strength**: Exploits conservative players, gets extra value
- **Weakness**: Risks losing everything if too greedy

**4. RankBasedAgent** (Hard)
```python
"""Adjusts aggression based on current rank - behind = more aggressive."""
def act(self, obs):
    my_rank = sum(1 for s in obs["all_player_scores"].values() if s > obs["player_score"]) + 1
    num_players = len(obs["all_player_scores"])
    
    # Base threshold varies by rank
    if my_rank == 1:  # Leading
        threshold = 40
    elif my_rank == num_players:  # Last place
        threshold = 100
    else:  # Middle
        threshold = 60
    
    if obs["can_bank"] and obs["current_bank"] >= threshold:
        return "bank"
    return "pass"
```
- **Strength**: Balanced, adapts to game state
- **Weakness**: Predictable thresholds

**Training Opponent Mix**:

```python
opponent_config = {
    "mode": "mixed",  # "self_play", "mixed", "curriculum"
    
    # Basic opponents (30% - for learning fundamentals)
    "basic": [
        {"type": "random", "weight": 0.10},
        {"type": "conservative", "weight": 0.10},
        {"type": "aggressive", "weight": 0.10},
    ],
    
    # Intermediate opponents (30% - for refinement)
    "intermediate": [
        {"type": "smart", "weight": 0.15},
        {"type": "adaptive", "weight": 0.15},
    ],
    
    # Advanced opponents (40% - for mastery)
    "advanced": [
        {"type": "leader_only", "weight": 0.10},
        {"type": "leader_plus_one", "weight": 0.10},
        {"type": "leech", "weight": 0.10},
        {"type": "rank_based", "weight": 0.10},
    ],
}
```

**Curriculum Learning Strategy** (Optional):
```python
curriculum_stages = [
    # Stage 1: Learn basics (episodes 0-2000)
    {"episodes": (0, 2000), 
     "opponents": ["random", "conservative", "aggressive"],
     "weights": [0.33, 0.33, 0.34]},
    
    # Stage 2: Face smarter opponents (episodes 2000-5000)
    {"episodes": (2000, 5000),
     "opponents": ["conservative", "aggressive", "smart", "adaptive"],
     "weights": [0.20, 0.20, 0.30, 0.30]},
    
    # Stage 3: Advanced opponents (episodes 5000+)
    {"episodes": (5000, float('inf')),
     "opponents": ["smart", "adaptive", "leader_only", "leader_plus_one", "leech"],
     "weights": [0.20, 0.20, 0.20, 0.20, 0.20]},
]
```

**Recommendation**: 
1. **Implement 4 advanced agents first** (LeaderOnly, LeaderPlusOne, Leech, RankBased)
2. **Start with mixed training** against all opponent types
3. **Optional**: Add curriculum if initial training struggles

#### C. Evaluation Protocol

```python
def evaluate_agent(agent, num_games=100, opponents=["smart", "aggressive"]):
    """Evaluate trained agent against strong opponents."""
    agent.training = False  # Disable exploration
    
    results = {
        "wins": 0,
        "avg_score": 0,
        "avg_rank": 0,
        "win_rate_vs": {},
    }
    
    for game in range(num_games):
        # Play against each opponent type
        # Track wins, scores, ranks
        pass
    
    agent.training = True  # Re-enable training
    return results
```

#### D. Logging & Monitoring

**TensorBoard Integration**:
```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter(f"runs/experiment_{timestamp}")

writer.add_scalar("train/episode_reward", episode_reward, episode)
writer.add_scalar("train/epsilon", agent.epsilon, episode)
writer.add_scalar("train/loss", loss, global_step)
writer.add_scalar("eval/win_rate", eval_results["win_rate"], episode)
writer.add_histogram("network/q_values", q_values, episode)
```

**Weights & Biases (Optional)**:
```python
import wandb

wandb.init(
    project="bank-dice-game",
    config={
        "architecture": network_config,
        "training": training_config,
        "reward": reward_config,
    }
)

wandb.log({"episode_reward": episode_reward, "epsilon": epsilon})
```

### 4. Configuration System

**Central config file** for all experiments:

```json
{
  "experiment": {
    "name": "dqn_dense_rewards_v1",
    "seed": 42,
    "num_episodes": 10000,
    "eval_freq": 100,
    "checkpoint_freq": 500
  },
  "environment": {
    "num_players": 4,
    "total_rounds": 10,
    "observation_type": "flat_vector",
    "reward_scheme": "dense",
    "reward_config": {
      "bank_reward_scale": 0.01,
      "seven_penalty_scale": 0.02,
      "win_bonus": 1.0
    }
  },
  "network": {
    "architecture": "mlp",
    "hidden_dims": [128, 128],
    "activation": "relu"
  },
  "training": {
    "gamma": 0.99,
    "epsilon_start": 1.0,
    "epsilon_end": 0.05,
    "epsilon_decay": 0.995,
    "learning_rate": 0.001,
    "batch_size": 64,
    "buffer_size": 100000,
    "target_update_freq": 100,
    "train_freq": 4
  },
  "opponents": {
    "mode": "mixed",
    "types": ["random", "conservative", "aggressive", "smart"],
    "weights": [0.2, 0.2, 0.3, 0.3]
  },
  "logging": {
    "tensorboard": true,
    "wandb": false,
    "log_dir": "logs",
    "checkpoint_dir": "checkpoints"
  }
}
```

## Implementation Plan

### Task 1: Advanced Opponent Agents (Priority: HIGH)

**Why First**: The DQN agent needs challenging opponents to train against. These advanced strategies will test the learning algorithm's ability to adapt.

**Deliverables**:
1. `LeaderOnlyAgent` - Only banks when becoming leader
2. `LeaderPlusOneAgent` - Leader strategy with +1 roll patience
3. `LeechAgent` - Shadows other players' banking decisions
4. `RankBasedAgent` - Adjusts threshold based on current rank

**Files**: `bank/agents/advanced_agents.py`

**Testing**:
- Unit tests for each strategy
- Integration test: tournament with all agents
- Verify agents implement `Agent` protocol correctly

**Estimated Time**: 0.5-1 day

### Task 2: Environment Wrapper (Priority: HIGH)

**Deliverables**:
1. `BankEnv` class with Gymnasium interface:
   - `reset()` - Initialize new game, return flattened observation
   - `step(action)` - Execute action, return (obs, reward, terminated, truncated, info)
   - `render()` - Optional visualization
2. Observation flattening:
   - `flatten_observation(obs: Observation) -> np.ndarray`
   - Uses existing `Observation` TypedDict from game engine
3. Reward calculation:
   - Tournament-based reward system (primary)
   - Sparse, dense, score-differential alternatives
   - Configurable via config file
4. Action masking:
   - `get_action_mask(obs: Observation) -> np.ndarray`
   - Prevents invalid actions (banking when can't bank)

**Files**: `bank/training/environment.py`

**Testing**:
- Unit tests for observation flattening
- Reward calculation tests (all schemes)
- Action masking validation
- Integration test: full episode with random agent
- Verify Gymnasium compatibility

**Estimated Time**: 1-2 days

### Task 3: DQN Agent (Priority: HIGH)

**Deliverables**:
1. `BankEnv` class with Gymnasium interface:
   - `reset()` - Initialize new game, return observation
   - `step(action)` - Execute action, return (obs, reward, terminated, truncated, info)
   - `render()` - Optional visualization
2. Observation encoding utilities:
   - `encode_observation(obs: Observation) -> np.ndarray`
   - Configurable encoding schemes
3. Reward calculation:
   - Multiple reward schemes (sparse, dense, risk-adjusted, opponent-relative)
   - Configurable via config file
4. Action masking:
   - `get_action_mask(obs: Observation) -> np.ndarray`
   - Prevent invalid actions

**Testing**:
- Unit tests for observation encoding
- Reward calculation tests
- Action masking validation
- Integration test: full episode playthrough

### Phase 4.2: DQN Agent (Priority: HIGH)

**Deliverables**:
1. `DQNetwork` neural network:
   - Configurable architecture (start with simple MLP)
   - Input: 14-dim observation vector
   - Output: 2 Q-values (pass, bank)
2. `ReplayBuffer`:
   - Store transitions (s, a, r, s', done)
   - Efficient sampling for batches
   - **Checkpoint-able**: Save/load entire buffer state
3. `DQNAgent` class:
   - Implements `Agent` protocol (compatible with game engine!)
   - Training methods: `store_transition()`, `train_step()`, `update_target()`
   - Epsilon-greedy exploration with decay
   - **Full checkpoint support**: Save network, optimizer, epsilon, buffer
4. Training utilities:
   - Huber loss calculation
   - Gradient clipping
   - Target network synchronization

**Files**: `bank/training/dqn_agent.py`

**Testing**:
- Network forward/backward pass
- Replay buffer operations (add, sample, save, load)
- Agent training step (gradient update)
- **Checkpoint integrity**: Save/load roundtrip
- Integration with game engine via `Agent` protocol
- Action masking respected during inference

**Estimated Time**: 2-3 days

### Task 4: Training Script (Priority: MEDIUM)

**Deliverables**:
1. `DQNetwork` neural network:
   - Configurable architecture (MLP, Dueling)
   - Forward pass returns Q-values
2. `ReplayBuffer`:
   - Store transitions (s, a, r, s', done)
   - Sample batches for training
3. `DQNAgent` class:
   - Implements `Agent` protocol
   - Training methods (store_transition, train_step, update_target)
   - Epsilon-greedy exploration
   - Save/load checkpoints
4. Training utilities:
   - Loss calculation (Huber loss)
   - Gradient updates
   - Target network synchronization

**Testing**:
- Network forward/backward pass
- Replay buffer operations
- Agent training step
- Save/load checkpoint integrity
- Integration with game engine

### Phase 4.3: Training Script (Priority: MEDIUM)

**Deliverables**:
1. Main training loop:
   - Episode iteration with tournament grouping
   - Experience collection
   - Training updates
   - Epsilon decay
   - **Signal handler for Ctrl+C graceful shutdown**
2. **Checkpoint system**:
   - Automatic periodic saves
   - Save on interruption (Ctrl+C)
   - Resume from checkpoint
   - Full state preservation (network, optimizer, buffer, stats)
3. Evaluation protocol:
   - Periodic evaluation against fixed opponents
   - Win rate, average score, rank tracking
   - Play against all advanced agents
4. Logging system:
   - TensorBoard integration
   - CSV logs for metrics
   - Checkpoint metadata
5. Config loading:
   - JSON config files
   - Command-line overrides
   - Config versioning
6. Opponent management:
   - Mixed opponent training
   - Configurable opponent weights
   - Optional curriculum learning

**Files**: `bank/training/train.py`, `bank/training/checkpoint.py`

**Testing**:
- Smoke test: train for 10 episodes
- **Interruption test**: Stop (Ctrl+C) and resume training
- Config loading/validation
- Checkpoint save/restore integrity
- Evaluation against rule-based agents
- Tournament reward calculation

**Estimated Time**: 2-3 days

**Deliverables**:
1. Main training loop:
   - Episode iteration
   - Experience collection
   - Training updates
   - Epsilon decay
2. Evaluation protocol:
   - Periodic evaluation against opponents
   - Win rate, average score, rank tracking
3. Logging system:
   - TensorBoard integration
   - CSV logs for metrics
   - Checkpoint management
4. Config loading:
   - JSON/YAML config files
   - Command-line overrides
5. Opponent management:
   - Mixed opponent training
   - Curriculum learning (optional)

**Testing**:
- Smoke test: train for 10 episodes
- Config loading/validation
- Checkpoint save/restore
- Evaluation against rule-based agents

## Key Design Principles

### 1. Flexibility First
- All hyperparameters in config files
- Multiple reward schemes selectable at runtime
- Easy to add new observation features

### 2. Reproducibility
- Deterministic seeding throughout
- Config versioning with experiments
- Checkpoint metadata includes config

### 3. Observability
- Rich logging (TensorBoard, W&B)
- Replay file generation for debugging
- Evaluation against fixed opponents

### 4. Modularity
- Clear separation: Env ↔ Agent ↔ Training
- Agent compatible with game engine (implements `Agent` protocol)
- Easy to swap reward functions, networks, opponents

### 5. Testing
- Unit tests for each component
- Integration tests for full training loop
- Smoke tests for quick validation

## Recommended Development Order

1. **Environment Wrapper** (1-2 days)
   - Start with flat observation vector
   - Implement sparse rewards first (simplest)
   - Add action masking
   - Test with random agent

2. **DQN Agent** (2-3 days)
   - Basic MLP network
   - Simple replay buffer
   - Standard DQN training
   - Test with manual environment

3. **Training Script** (1-2 days)
   - Basic training loop
   - TensorBoard logging
   - Checkpoint saving
   - Evaluation vs rule-based agents

4. **Refinement** (1-2 days)
   - Add dense reward schemes
   - Experiment with network architectures
   - Tune hyperparameters
   - Compare against smart agents

5. **Documentation** (1 day)
   - Training guide
   - Hyperparameter tuning tips
   - Experiment tracking best practices

## Open Questions & Design Decisions

### ✅ Resolved (Based on Your Feedback):

1. **Observation Design**: ✅ Use existing `Observation` TypedDict, flatten to 14-dim vector
2. **Reward Scheme**: ✅ Start with **tournament-based** rewards (every 5 games) to handle variance
3. **Training Interruption**: ✅ Full checkpoint system with Ctrl+C handling
4. **Advanced Opponents**: ✅ Implement 4 hard strategies (LeaderOnly, LeaderPlusOne, Leech, RankBased)

### 🤔 Still To Discuss:

1. **Tournament Size**: How many games per tournament reward?
   - Option A: 5 games (your suggestion - faster feedback)
   - Option B: 10 games (more stable, less variance)
   - Option C: Configurable (start with 5, tune later)

2. **Tournament Reward Formula**: How to weight different components?
   ```python
   # Current proposal:
   reward = (win_rate * 2.0) + ((4 - avg_rank) / 3.0) + (consistency_bonus)
   
   # Alternatives:
   # More rank-focused: reward = (4 - avg_rank) * 1.5
   # More win-focused: reward = win_rate * 3.0 - loss_rate * 1.0
   ```

3. **Network Architecture**: Start simple or add complexity?
   - Option A: Simple MLP (128→128→2) - **Recommended**
   - Option B: Dueling DQN (separate value/advantage streams)
   - Option C: Noisy Networks (learned exploration)

4. **Opponent Mix During Training**: How to balance opponents?
   - Option A: Equal weights across all 10 agents (10% each)
   - Option B: Weighted by difficulty (40% advanced, 30% intermediate, 30% basic)
   - Option C: Curriculum (start basic, increase difficulty)

5. **Evaluation Metric**: What defines "good enough" performance?
   - Win rate vs SmartAgent: 40%? 50%? 60%?
   - Win rate vs all agents averaged: 30%? 35%?
   - Positive expected score differential?
   - Consistently ranks in top 2 in 4-player games?

6. **Training Duration**: How many episodes?
   - Initial training: 10,000 episodes?
   - Full training: 50,000-100,000 episodes?
   - Depends on convergence speed

7. **Replay Buffer Size**: How much experience to store?
   - Small: 10,000 transitions (faster, less memory)
   - Medium: 100,000 transitions (balanced) - **Recommended**
   - Large: 1,000,000 transitions (more diversity, more memory)

### 💡 Recommendations:

**For Initial Implementation**:
- Tournament size: **5 games** (configurable)
- Reward formula: **Balanced** (win_rate + rank + consistency)
- Network: **Simple MLP** (128→128)
- Opponents: **Weighted by difficulty** (40% advanced)
- Success: **>40% win rate vs SmartAgent**
- Training: **10,000 episodes** initial run
- Buffer: **100,000 transitions**

**Philosophy**: Start simple, measure, iterate. The architecture is designed to make experimentation easy.

## Success Criteria

Phase 4 is complete when:

- ✅ Environment wrapper passes all tests
- ✅ DQN agent can play full games using `Agent` protocol
- ✅ Training script completes 1000 episodes without errors
- ✅ Checkpoints can be loaded and played via CLI
- ✅ Agent achieves >40% win rate vs SmartAgent after training
- ✅ All hyperparameters configurable via JSON
- ✅ TensorBoard logs show learning progress
- ✅ Documentation explains how to run experiments

## Next Steps

1. Review this architecture document
2. Discuss open questions and design decisions
3. Finalize reward scheme and observation encoding
4. Begin implementation with Task 1 (Environment Wrapper)
5. Iterate with frequent testing and evaluation
