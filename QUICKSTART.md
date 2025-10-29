# BANK! Quick Start Guide

## Installation

```bash
# Basic installation
pip install -e .

# With ML support for DQN training
pip install -e ".[ml]"

# With development tools
pip install -e ".[dev]"
```

## Playing the Game

### Interactive Play (Human vs AI)
```bash
bank play --players 2 --human 1 --rule-based 1
```

### Demo (AI vs AI)
```bash
bank demo
```

### Custom Game Setup
```bash
# 3 players: 1 human, 1 random bot, 1 rule-based bot
bank play --players 3 --human 1 --random 1 --rule-based 1
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
from bank.agents.base import BaseAgent
from bank.game.state import GameState

class MyAgent(BaseAgent):
    def select_action(self, game_state, valid_actions):
        # Your strategy here
        player = game_state.players[self.player_id]
        
        # Example: Always bank high-value cards
        if "bank_card" in valid_actions and player.hand:
            for idx, card in enumerate(player.hand):
                if card > 40:
                    return ("bank_card", {"card_idx": idx})
        
        # Default action
        if valid_actions:
            return (valid_actions[0], {})
        return ("pass", {})
```

### Using Your Agent
```python
from bank.game.engine import BankGame
from bank.cli.game_runner import GameRunner

# Create game
game = BankGame(num_players=2, player_names=["MyBot", "RandomBot"])

# Create agents
from bank.agents.random_agent import RandomAgent
agents = [
    MyAgent(player_id=0, name="MyBot"),
    RandomAgent(player_id=1, name="RandomBot")
]

# Run game
runner = GameRunner(game, agents)
runner.run()
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

1. **Testing your agent**: Use `bank demo` with your custom agent to see it in action
2. **Debugging**: Add print statements in your agent's `select_action` method
3. **Training**: Start with fewer episodes (100-500) to test, then scale up
4. **Agents**: Study `rule_based.py` for inspiration on manual agent strategies

## Common Issues

**"Gymnasium not found"**: Install ML dependencies with `pip install -e ".[ml]"`
**"PyTorch not found"**: Same as above - use the ML extras
**"Command not found"**: Make sure you installed with `pip install -e .`

## Next Steps

The project includes a basic game framework with simplified mechanics. To use it for the actual BANK! game:

1. **Implement actual BANK! game rules** in `bank/game/engine.py` (current version has placeholder mechanics)
2. Create more sophisticated agents based on the real rules
3. Train DQN agents and compare strategies
4. Build a tournament system to evaluate agents

**Note:** The framework is complete and ready - you just need to add the specific BANK! game rules to the engine.

Enjoy building agents for BANK! 🎮🃏
