# Examples

This directory contains example scripts demonstrating how to use the BANK! dice game framework.

## About BANK!

BANK! is a dice rolling game where players compete to accumulate points by banking strategically. Each round, players decide whether to bank (secure) the current round value or continue playing. The game features special rules for doubles and sevens that create interesting risk/reward dynamics.

## Available Examples

### `simple_agent.py`
Demonstrates how to create custom agents with different strategies:
- **CautiousAgent**: Adaptive threshold-based strategy that adjusts based on roll count and competitive position
- **AlwaysBankAt100**: Minimal example showing the simplest possible banking strategy

Shows the Agent interface: `act(observation) -> Action`

```bash
python examples/simple_agent.py
```

### `inspect_game.py`
Demonstrates programmatic game execution and state inspection:
- How to access round state (roll count, bank value, active players)
- How to analyze player states (scores, banking status)
- How to inspect dice rolls and special events
- Example analysis functions for game statistics

```bash
python examples/inspect_game.py
```

### `tournament.py`
Shows how to run batch tournaments and collect statistics:
- Programmatic tournament execution (50-100 games)
- Statistical analysis (win rates, average scores)
- Strategy comparison across all agent types
- Head-to-head matchups

```bash
python examples/tournament.py
```

### `replay_demo.py`
Demonstrates game replay recording and analysis:
- How to record games using GameRecorder
- Saving and loading replays from JSON files
- Multiple replay viewing modes (summary, play-by-play, round analysis)
- Player statistics extraction (banking patterns, decision metrics)

```bash
python examples/replay_demo.py
```

## Available Agent Types

The framework includes 6 built-in agent types:

1. **RandomAgent**: Random decisions (baseline)
2. **ThresholdAgent**: Banks at a fixed threshold value
3. **ConservativeAgent**: Cautious, banks early to minimize risk
4. **AggressiveAgent**: Takes more chances, pursues higher scores
5. **SmartAgent**: Context-aware, considers game position and roll count
6. **AdaptiveAgent**: Dynamically adjusts strategy based on round progression

## Agent Interface

All agents implement the `Agent` protocol:

```python
from bank.agents.base import Agent, Action, Observation

class MyAgent:
    def __init__(self, player_id: int, name: str):
        self.player_id = player_id
        self.name = name
    
    def act(self, observation: Observation) -> Action:
        """Decide whether to 'bank' or 'pass' based on observation."""
        # Your strategy here
        if observation["current_bank"] >= 50:
            return "bank"
        return "pass"
    
    def reset(self) -> None:
        """Reset agent state for a new game."""
        pass
```

### Observation Structure

The `Observation` TypedDict provides all game state information:

```python
{
    "round_number": int,           # Current round (1-based)
    "roll_count": int,             # Number of rolls this round
    "current_bank": int,           # Points in the bank this round
    "last_roll": tuple[int, int],  # Most recent dice roll
    "active_player_ids": list[int], # Players still active this round
    "player_id": int,              # Your player ID
    "player_score": int,           # Your total score
    "can_bank": bool,              # Whether you can bank this round
    "all_player_scores": dict[int, int], # All player scores
}
```

## Creating Your Own Agents

Here are some ideas for custom agents:

1. **Position-Aware**: Adjust aggression based on whether you're leading/trailing
2. **Risk-Calculated**: Use probability to assess roll outcomes
3. **Opponent-Modeling**: Adapt based on other players' behavior
4. **Round-Specific**: Different strategies for early vs late rounds
5. **Combo-Hunter**: Specifically target doubles and sevens bonuses
6. **Statistical**: Track historical outcomes to inform decisions

## Running Examples

Make sure the package is installed first:

```bash
# From the repository root
pip install -e .

# Then run any example
python examples/simple_agent.py
python examples/inspect_game.py
python examples/tournament.py
python examples/replay_demo.py
```

## Replay System

The replay system allows you to record games for later analysis:

### Recording Games

```python
from bank.replay.recorder import GameRecorder, save_replay
from bank.game.engine import BankGame

# Create recorder
recorder = GameRecorder()

# Create game with recorder attached
game = BankGame(num_players=4, agents=your_agents, recorder=recorder)
game.play_game()

# Save replay to file
save_replay(recorder, "game_001.json")
```

### Viewing Replays

```python
from bank.replay.recorder import load_replay
from bank.replay.viewer import ReplayViewer

# Load replay
replay_data = load_replay("game_001.json")
viewer = ReplayViewer(replay_data)

# Display summary
viewer.print_summary()

# Show play-by-play narrative
viewer.print_play_by_play()

# Analyze specific round
viewer.analyze_round(3)

# Get player statistics
viewer.print_player_stats(player_id=0)
```

Replays are saved as human-readable JSON files containing all game events with timestamps.

## CLI vs Programmatic Usage

- **CLI**: Interactive play with `bank play`, `bank demo`, `bank tournament`
  - Human vs AI games
  - Visual feedback and game state display
  - Configurable delays and timeouts

- **Programmatic**: Script-based execution (these examples)
  - Batch processing (tournaments)
  - Statistical analysis
  - Custom logging and metrics
  - Agent development and testing

Both approaches use the same game engine and agent interface!
