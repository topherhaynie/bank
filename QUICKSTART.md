# BANK! Quick Start Guide

## Installation

```bash
# Basic installation
pip install -e .

# With ML support for DQN training (in development)
pip install -e ".[ml]"

# With development tools
pip install -e ".[dev]"
```

## Playing the Game

### Interactive Play (Human vs AI)
```bash
# 2 players: you vs a smart AI
bank play --players 2 --human 1 --smart 1

# 4 players: you vs 3 different AI strategies
bank play --players 4 --human 1 --conservative 1 --aggressive 1 --smart 1
```

### Demo (AI vs AI)
```bash
# Watch 4 AI agents compete
bank demo

# Custom demo with more rounds
bank demo --rounds 5
```

### Tournament Mode
```bash
# Run 100 games and see which strategy wins most
bank tournament --games 100

# Longer tournament with more rounds per game
bank tournament --games 50 --rounds 10
```

### Custom Game Setup
```bash
# 3 players with specific configurations
bank play --players 3 --human 1 --adaptive 1 --random 1 --rounds 7

# Reproducible game with seed
bank play --players 2 --human 1 --smart 1 --seed 42

# Fast-paced game with no delays
bank play --players 4 --aggressive 4 --delay 0
```

## Training AI Agents

### Train a DQN Agent
```bash
# Requires ML dependencies: pip install -e ".[ml]"
bank-train --episodes 5000 --save-path models/my_agent.pth
```

### Resume Training
```bash
bank-train --episodes 5000 --load-path models/my_agent.pth --save-path models/my_agent_v2.pth
```

## Creating Custom Agents

### Simple Rule-Based Agent
```python
from bank.agents.base import Agent, Action, Observation

class MyAgent:
    def __init__(self, player_id: int, name: str):
        self.player_id = player_id
        self.name = name
    
    def act(self, observation: Observation) -> Action:
        """Decide whether to 'bank' or 'pass'."""
        # Example: Bank if we have 60+ points or after 3 rolls
        if observation["current_bank"] >= 60:
            return "bank"
        if observation["roll_count"] >= 3:
            return "bank"
        return "pass"
    
    def reset(self) -> None:
        """Reset agent state for a new game."""
        pass
```

### Using Your Agent in a Game
```python
from bank.game.engine import BankGame
from bank.agents.random_agent import RandomAgent

# Create game
game = BankGame(
    num_players=3,
    player_names=["MyBot", "RandomBot", "AnotherBot"],
    total_rounds=5
)

# Create agents
agents = [
    MyAgent(player_id=0, name="MyBot"),
    RandomAgent(player_id=1, name="RandomBot", seed=42),
    MyAgent(player_id=2, name="AnotherBot")
]

# Set agents and play
game.agents = agents
game.play_game()

# Check results
for player in game.state.players:
    print(f"{player.name}: {player.score} points")
```

### Advanced: Position-Aware Agent
```python
class SmartAgent:
    def __init__(self, player_id: int, name: str):
        self.player_id = player_id
        self.name = name
    
    def act(self, observation: Observation) -> Action:
        """Adaptive strategy based on game position."""
        bank = observation["current_bank"]
        my_score = observation["player_score"]
        all_scores = observation["all_player_scores"]
        roll_count = observation["roll_count"]
        
        # Get max opponent score
        max_opponent = max(s for pid, s in all_scores.items() 
                          if pid != self.player_id)
        
        # If we're behind, take more risks
        if my_score < max_opponent:
            threshold = 80
        else:
            threshold = 50
        
        # Bank if we meet threshold or too many rolls
        if bank >= threshold or roll_count >= 4:
            return "bank"
        return "pass"
    
    def reset(self) -> None:
        pass
```

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/game/test_engine.py

# With coverage
pytest --cov=bank --cov-report=html
```

## Code Formatting

```bash
# Format code
black bank/ tests/

# Check style
flake8 bank/ tests/

# Type checking
mypy bank/
```

## Project Structure

```
bank/
├── bank/              # Main package
│   ├── game/         # Game engine
│   ├── agents/       # Agent implementations
│   ├── cli/          # Command-line interface
│   ├── training/     # DQN training framework
│   └── utils/        # Utilities
└── tests/            # Test suite
```

## Configuration

Create `config.json` from the example:
```bash
cp config.example.json config.json
# Edit config.json with your preferred settings
```

## Tips

1. **Testing your agent**: Use the examples in `examples/` as templates
2. **Debugging**: Add print statements in your agent's `act` method to see decisions
3. **Strategy development**: Run tournaments with `bank tournament` to compare agents
4. **Observation details**: Check `docs/AGENT_API.md` for complete observation documentation

## Common Issues

**"Command not found"**: Make sure you installed with `pip install -e .`
**"ModuleNotFoundError: No module named 'bank'"**: Install the package or activate your venv
**"Gymnasium not found"**: ML features are in development, install with `pip install -e ".[ml]"` when available

## Available Agent Types

The game includes 6 built-in agent strategies:

1. **RandomAgent**: Random decisions (baseline)
2. **ThresholdAgent**: Banks at a fixed point value
3. **ConservativeAgent**: Risk-averse, banks early
4. **AggressiveAgent**: Takes chances for higher scores
5. **SmartAgent**: Context-aware with adaptive thresholds
6. **AdaptiveAgent**: Adjusts based on competitive position

Study these in `bank/agents/rule_based.py` for inspiration!

## Next Steps

1. **Play interactively**: Get familiar with the game using `bank play`
2. **Study examples**: Check `examples/` directory for custom agent patterns
3. **Build your agent**: Start with a simple threshold strategy
4. **Test with tournaments**: Run `bank tournament` to evaluate performance
5. **Iterate**: Refine your strategy based on results

Enjoy building agents for BANK! �
