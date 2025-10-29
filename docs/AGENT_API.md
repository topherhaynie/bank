# Agent API Reference

This document provides a comprehensive reference for implementing agents that play BANK! (dice variant).

## Table of Contents
- [Overview](#overview)
- [Agent Interface](#agent-interface)
- [Observation Structure](#observation-structure)
- [Action Types](#action-types)
- [Implementation Guide](#implementation-guide)
- [Examples](#examples)
- [Testing Your Agent](#testing-your-agent)

## Overview

BANK! agents make decisions by implementing a simple interface: receive an observation of the game state and return an action ("bank" or "pass"). The game engine handles all state management, rule enforcement, and game flow.

### Key Concepts

- **Observation**: A dictionary containing all information visible to the agent
- **Action**: A string literal, either `"bank"` or `"pass"`
- **Polling**: The engine polls agents for decisions after each dice roll
- **Banking**: When an agent banks, they claim the current bank value and exit the round

## Agent Interface

All agents must inherit from the `Agent` abstract base class and implement the `act` method.

### Base Class

```python
from bank.agents.base import Agent, Observation, Action

class MyAgent(Agent):
    """Your custom agent implementation."""
    
    def __init__(self, player_id: int, name: str | None = None):
        """Initialize the agent.
        
        Args:
            player_id: Unique identifier for this player (0-based)
            name: Optional name for display purposes
        """
        super().__init__(player_id, name)
        # Add any custom initialization here
    
    def act(self, observation: Observation) -> Action:
        """Make a decision based on the current game state.
        
        Args:
            observation: Complete game state information
            
        Returns:
            Either "bank" or "pass"
        """
        # Your decision logic here
        return "pass"
    
    def reset(self) -> None:
        """Optional: Reset agent state for a new game.
        
        Called at the start of each new game. Override this if your
        agent maintains internal state (e.g., learning statistics).
        """
        # Reset any internal state here
        pass
```

### Required Methods

#### `act(observation: Observation) -> Action`

The core decision-making method. Called whenever the agent needs to make a decision.

**Parameters:**
- `observation`: A dictionary containing all relevant game state information

**Returns:**
- `"bank"`: Claim the current bank value and exit this round
- `"pass"`: Continue playing this round

**Important:**
- If `observation["can_bank"]` is `False`, returning `"bank"` will be ignored
- This method should be fast; slow agents may delay gameplay or training

#### `reset() -> None` (Optional)

Called at the start of each new game. Override if your agent needs to reset internal state.

## Observation Structure

The `Observation` TypedDict provides complete information about the current game state.

### Type Definition

```python
from typing import TypedDict

class Observation(TypedDict):
    """Observation provided to agents."""
    round_number: int
    roll_count: int
    current_bank: int
    last_roll: tuple[int, int] | None
    active_player_ids: set[int]
    player_id: int
    player_score: int
    can_bank: bool
    all_player_scores: dict[int, int]
```

### Field Descriptions

| Field | Type | Description | Valid Values |
|-------|------|-------------|--------------|
| `round_number` | `int` | Current round number (1-based) | 1 to `total_rounds` |
| `roll_count` | `int` | Number of rolls in current round (1-based) | 1+ |
| `current_bank` | `int` | Points currently in the bank | 0+ |
| `last_roll` | `tuple[int, int] \| None` | Most recent dice roll `(die1, die2)` | Each die: 1-6, or `None` at round start |
| `active_player_ids` | `set[int]` | Player IDs still active in this round | Subset of all player IDs |
| `player_id` | `int` | This agent's player ID | 0-based index |
| `player_score` | `int` | This agent's total score | 0+ |
| `can_bank` | `bool` | Whether this agent can bank | `True` or `False` |
| `all_player_scores` | `dict[int, int]` | All players' scores | Maps player_id → score |

### Field Details

#### `round_number`
The current round in the game (1-based indexing). Games typically have 10, 15, or 20 rounds.

```python
# Example usage
if observation["round_number"] <= 3:
    # Early game strategy
    pass
elif observation["round_number"] >= total_rounds - 2:
    # Late game strategy
    pass
```

#### `roll_count`
How many rolls have occurred in the current round (1-based). Important for understanding special rules:
- Rolls 1-3: Sevens add 70 points; doubles add their sum
- Rolls 4+: Sevens end the round; doubles double the bank

```python
# Example usage
if observation["roll_count"] <= 3:
    # Still in the "safe" period
    threshold = 50
else:
    # Risk of seven increases
    threshold = 30
```

#### `current_bank`
The number of points currently available to claim. This is the amount you would score if you bank now.

```python
# Example usage
if observation["current_bank"] >= 100:
    return "bank"  # Good value, claim it!
```

#### `last_roll`
The most recent dice roll as a tuple `(die1, die2)`, or `None` if no roll has occurred yet this round.

```python
# Example usage
if observation["last_roll"]:
    die1, die2 = observation["last_roll"]
    if die1 == die2:
        # Doubles were just rolled
        if observation["roll_count"] > 3:
            # Bank just doubled! Might want to claim it
            pass
```

**Important:** Each die shows 1-6. Key combinations:
- Sum == 7: Ends round (after roll 3) or adds 70 (first 3 rolls)
- Doubles (die1 == die2): Doubles bank (after roll 3) or adds sum (first 3 rolls)

#### `active_player_ids`
Set of player IDs who haven't banked yet this round. Includes your own ID if you haven't banked.

```python
# Example usage
num_active = len(observation["active_player_ids"])
if num_active == 1:
    # You're the last player - more risky!
    return "bank"  # Play it safe
```

#### `player_id`
Your agent's unique identifier (0-based). Use this to find your own information in shared data structures.

```python
# Example usage
my_score = observation["all_player_scores"][observation["player_id"]]
# Note: This is the same as observation["player_score"]
```

#### `player_score`
Your current total score across all rounds. This is your cumulative score, not including the current bank (you must bank to add it).

```python
# Example usage
my_score = observation["player_score"]
opponent_scores = [
    score for pid, score in observation["all_player_scores"].items()
    if pid != observation["player_id"]
]
if my_score < max(opponent_scores):
    # Behind - need to take risks
    threshold = 80
else:
    # Leading - play conservatively
    threshold = 40
```

#### `can_bank`
Boolean indicating whether you're allowed to bank. This is `False` if you've already banked this round.

```python
# Example usage
if not observation["can_bank"]:
    # Already banked - must pass
    return "pass"

if observation["current_bank"] >= threshold:
    return "bank"  # Only executed if can_bank is True
```

**Important:** If you return `"bank"` when `can_bank` is `False`, the engine will ignore your action and treat it as `"pass"`.

#### `all_player_scores`
Dictionary mapping each player ID to their current total score. Useful for competitive strategy.

```python
# Example usage
scores = observation["all_player_scores"]
my_score = scores[observation["player_id"]]
leader_score = max(scores.values())

if leader_score - my_score > 100:
    # Way behind - need aggressive strategy
    return "pass"  # Keep rolling for bigger bank
```

## Action Types

Actions are defined using Python's `Literal` type for type safety.

### Type Definition

```python
from typing import Literal

Action = Literal["bank", "pass"]
```

### Available Actions

#### `"bank"`
Claim the current bank value and exit this round.

**When to use:**
- Current bank value is good enough for your strategy
- Risk of losing the bank is too high
- You're satisfied with your position

**What happens:**
1. `observation["current_bank"]` is added to your total score
2. You're removed from `active_player_ids` for this round
3. You won't be asked to make decisions until the next round
4. The bank remains available for other players (they can also bank the same value)

**Example scenarios:**
```python
# Bank when reaching a threshold
if observation["current_bank"] >= 50:
    return "bank"

# Bank if you're the last player
if len(observation["active_player_ids"]) == 1:
    return "bank"

# Bank after roll 3 to avoid seven risk
if observation["roll_count"] > 3 and observation["current_bank"] > 20:
    return "bank"
```

#### `"pass"`
Continue playing this round without banking.

**When to use:**
- Current bank is too low
- You're willing to risk it for a higher value
- It's still early in the round (roll count <= 3)

**What happens:**
1. Your score doesn't change
2. You remain in `active_player_ids`
3. The game continues with more dice rolls
4. You'll be polled again after the next roll (if round hasn't ended)

**Example scenarios:**
```python
# Pass when bank is too low
if observation["current_bank"] < 30:
    return "pass"

# Pass during safe early rolls
if observation["roll_count"] <= 3:
    return "pass"

# Pass when can't bank anyway
if not observation["can_bank"]:
    return "pass"
```

## Implementation Guide

### Step-by-Step Implementation

1. **Import required types**
   ```python
   from bank.agents.base import Agent, Action, Observation
   ```

2. **Create your agent class**
   ```python
   class MyAgent(Agent):
       def __init__(self, player_id: int, name: str | None = None):
           super().__init__(player_id, name)
   ```

3. **Implement the act method**
   ```python
   def act(self, observation: Observation) -> Action:
       # Your logic here
       return "pass"
   ```

4. **Add any internal state** (optional)
   ```python
   def __init__(self, player_id: int, name: str | None = None):
       super().__init__(player_id, name)
       self.risk_tolerance = 0.7
       self.stats = {"banks": 0, "passes": 0}
   ```

5. **Implement reset if needed** (optional)
   ```python
   def reset(self) -> None:
       self.stats = {"banks": 0, "passes": 0}
   ```

### Best Practices

✅ **Do:**
- Check `can_bank` before returning `"bank"`
- Use type hints for clarity
- Keep decision logic fast (< 1ms preferred)
- Handle edge cases (no last_roll, single active player, etc.)
- Add docstrings explaining your strategy

❌ **Don't:**
- Return anything other than `"bank"` or `"pass"`
- Modify the observation dictionary
- Maintain state that affects other games (unless you reset it)
- Make network calls or file I/O in `act()`
- Raise exceptions (return valid action or handle errors internally)

### Common Patterns

#### Threshold Strategy
```python
def act(self, observation: Observation) -> Action:
    """Bank when bank reaches a threshold."""
    if not observation["can_bank"]:
        return "pass"
    
    if observation["current_bank"] >= self.threshold:
        return "bank"
    return "pass"
```

#### Risk-Aware Strategy
```python
def act(self, observation: Observation) -> Action:
    """Consider risk based on roll count."""
    if not observation["can_bank"]:
        return "pass"
    
    # After roll 3, sevens become dangerous
    if observation["roll_count"] > 3:
        # Lower threshold due to risk
        threshold = 40
    else:
        # Safe period, can be greedy
        threshold = 80
    
    if observation["current_bank"] >= threshold:
        return "bank"
    return "pass"
```

#### Competitive Strategy
```python
def act(self, observation: Observation) -> Action:
    """Adjust strategy based on relative position."""
    if not observation["can_bank"]:
        return "pass"
    
    my_score = observation["player_score"]
    opponent_scores = [
        s for pid, s in observation["all_player_scores"].items()
        if pid != observation["player_id"]
    ]
    leader_score = max(opponent_scores) if opponent_scores else 0
    
    # If behind, take more risks
    if my_score < leader_score:
        threshold = 60
    else:
        threshold = 40
    
    if observation["current_bank"] >= threshold:
        return "bank"
    return "pass"
```

## Examples

### Example 1: Simple Random Agent

```python
import random
from bank.agents.base import Agent, Action, Observation

class RandomAgent(Agent):
    """Agent that randomly decides to bank or pass."""
    
    def __init__(self, player_id: int, name: str | None = None, seed: int | None = None):
        super().__init__(player_id, name or f"Random-{player_id}")
        self.rng = random.Random(seed)
    
    def act(self, observation: Observation) -> Action:
        """Randomly choose to bank or pass."""
        if not observation["can_bank"]:
            return "pass"
        
        # 50/50 chance
        return "bank" if self.rng.random() < 0.5 else "pass"
    
    def reset(self) -> None:
        """Reset RNG if needed."""
        # RNG maintains its state, no reset needed
        pass
```

### Example 2: Threshold Agent

```python
from bank.agents.base import Agent, Action, Observation

class ThresholdAgent(Agent):
    """Agent that banks when bank reaches a threshold."""
    
    def __init__(self, player_id: int, threshold: int = 50, name: str | None = None):
        super().__init__(player_id, name or f"Threshold-{threshold}")
        self.threshold = threshold
    
    def act(self, observation: Observation) -> Action:
        """Bank if current bank meets or exceeds threshold."""
        if observation["can_bank"] and observation["current_bank"] >= self.threshold:
            return "bank"
        return "pass"
```

### Example 3: Smart Agent

```python
from bank.agents.base import Agent, Action, Observation

class SmartAgent(Agent):
    """Agent with adaptive strategy based on game context."""
    
    def __init__(self, player_id: int, name: str | None = None):
        super().__init__(player_id, name or f"Smart-{player_id}")
    
    def act(self, observation: Observation) -> Action:
        """Make context-aware banking decisions."""
        if not observation["can_bank"]:
            return "pass"
        
        bank = observation["current_bank"]
        roll_count = observation["roll_count"]
        num_active = len(observation["active_player_ids"])
        
        # Early rolls: be greedy
        if roll_count <= 3:
            threshold = 100
        # Late rolls: be conservative
        elif roll_count >= 6:
            threshold = 30
        # Middle rolls: moderate
        else:
            threshold = 60
        
        # Last player: always bank if there's anything
        if num_active == 1 and bank > 0:
            return "bank"
        
        # Check threshold
        if bank >= threshold:
            return "bank"
        
        return "pass"
```

### Example 4: Learning Agent Template

```python
from bank.agents.base import Agent, Action, Observation

class LearningAgent(Agent):
    """Template for agents that learn from experience."""
    
    def __init__(self, player_id: int, name: str | None = None):
        super().__init__(player_id, name or f"Learner-{player_id}")
        self.episode_history = []
        self.stats = {"total_banked": 0, "rounds_played": 0}
    
    def act(self, observation: Observation) -> Action:
        """Make decision and record experience."""
        # Store experience for learning
        self.episode_history.append({
            "observation": observation.copy(),
            "timestamp": len(self.episode_history)
        })
        
        # Your decision logic here
        action = self._compute_action(observation)
        
        return action
    
    def _compute_action(self, observation: Observation) -> Action:
        """Internal method for decision logic."""
        # Implement your learning-based decision here
        if observation["can_bank"] and observation["current_bank"] >= 50:
            return "bank"
        return "pass"
    
    def reset(self) -> None:
        """Reset for new game and process learning."""
        # Process episode for learning
        self._learn_from_episode()
        
        # Reset episode history
        self.episode_history = []
    
    def _learn_from_episode(self) -> None:
        """Update model/statistics based on episode history."""
        # Implement learning logic here
        pass
```

## Testing Your Agent

### Unit Testing

Test your agent in isolation:

```python
from bank.agents.base import Observation

def test_my_agent():
    """Test agent decision logic."""
    agent = MyAgent(player_id=0)
    
    # Create a test observation
    observation: Observation = {
        "round_number": 1,
        "roll_count": 4,
        "current_bank": 60,
        "last_roll": (3, 4),
        "active_player_ids": {0, 1},
        "player_id": 0,
        "player_score": 20,
        "can_bank": True,
        "all_player_scores": {0: 20, 1: 15}
    }
    
    # Test decision
    action = agent.act(observation)
    assert action in ["bank", "pass"]
    
    # Test specific logic
    if observation["current_bank"] >= agent.threshold:
        assert action == "bank"
```

### Integration Testing

Test your agent with the game engine:

```python
from bank.game.engine import BankGame

def test_agent_integration():
    """Test agent playing a full game."""
    agents = [MyAgent(0), MyAgent(1)]
    game = BankGame(
        num_players=2,
        agents=agents,
        total_rounds=5,
        rng=random.Random(42)  # For reproducibility
    )
    
    # Play the game
    game.play_game()
    
    # Check results
    assert game.state.is_game_over()
    winner = game.get_winner()
    assert winner is not None
```

### Debugging Tips

1. **Print observations**: Add debug prints to see what your agent sees
   ```python
   def act(self, observation: Observation) -> Action:
       print(f"Player {observation['player_id']}: "
             f"Bank={observation['current_bank']}, "
             f"Roll={observation['roll_count']}")
       # Your logic
   ```

2. **Test edge cases**: Handle all possible observation states
   - First roll of round (no `last_roll`)
   - Already banked (`can_bank=False`)
   - Last active player
   - Zero bank value

3. **Use deterministic testing**: Seed RNG for reproducible tests
   ```python
   import random
   rng = random.Random(42)
   agent = MyAgent(player_id=0, seed=42)
   game = BankGame(num_players=2, agents=[agent], rng=rng)
   ```

4. **Check type compliance**: Use type checkers
   ```bash
   mypy bank/agents/my_agent.py
   ```

## Next Steps

- **Read the game rules**: See `docs/BASE_GAME_RULES.md` for complete game mechanics
- **Study examples**: Check `bank/agents/test_agents.py` for more examples
- **Run tournaments**: Use `examples/tournament.py` to test your agent against others
- **Train ML agents**: See `bank/training/` for reinforcement learning setup

## Additional Resources

- **Architecture**: `docs/ARCHITECTURE.md` - System design overview
- **Conventions**: `docs/CONVENTIONS.md` - Code style and patterns
- **Project Plan**: `docs/PROJECT_PLAN.md` - Implementation roadmap
- **Game Rules**: `docs/BASE_GAME_RULES.md` - Complete game mechanics

---

*This documentation reflects the BANK! dice variant implementation as of October 2025.*
