# BANK! 🎮🃏

A modular Python game environment for the card game BANK! with support for manual agents, AI training (DQN), and CLI gameplay.

## Features

- 🎯 **Game Engine**: Complete BANK! game implementation with state management
- 🤖 **Agent Support**: 
  - Manual/programmed agents (random, rule-based)
  - Deep Q-Network (DQN) reinforcement learning agents
  - Easy-to-extend base agent interface
- 🖥️ **CLI Interface**: Interactive command-line gameplay
- 🧠 **Training Framework**: Gymnasium-compatible environment for RL training
- 🧪 **Testing**: Comprehensive test suite with pytest

## Project Structure

```
bank/
├── bank/                      # Main package
│   ├── game/                  # Game engine and rules
│   │   ├── engine.py         # Core game logic
│   │   └── state.py          # Game state management
│   ├── agents/                # Agent implementations
│   │   ├── base.py           # Base agent interface
│   │   ├── random_agent.py   # Random baseline agent
│   │   └── rule_based.py     # Rule-based agent template
│   ├── cli/                   # Command-line interface
│   │   ├── main.py           # CLI entry point
│   │   ├── human_player.py   # Human player interaction
│   │   └── game_runner.py    # Game orchestration
│   ├── training/              # RL training framework
│   │   ├── environment.py    # Gymnasium wrapper
│   │   ├── dqn_agent.py      # DQN implementation
│   │   └── train.py          # Training script
│   └── utils/                 # Utilities
│       └── config.py         # Configuration management
├── tests/                     # Test suite
├── pyproject.toml            # Project configuration
└── config.example.json       # Example configuration

```

## Installation

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/topherhaynie/bank.git
cd bank

# Install the package
pip install -e .
```

### Installation with ML Dependencies

For DQN training and reinforcement learning features:

```bash
pip install -e ".[ml]"
```

### Development Installation

For development with testing and linting tools:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Play Against AI

```bash
# Play as a human against a rule-based AI
bank play --players 2 --human 1 --rule-based 1

# Watch AI agents play against each other
bank demo
```

### Train a DQN Agent

```bash
# Train a DQN agent (requires ML dependencies)
bank-train --episodes 5000 --save-path models/my_agent.pth
```

### Create Custom Agents

```python
from bank.agents.base import BaseAgent
from bank.game.state import GameState

class MyCustomAgent(BaseAgent):
    def select_action(self, game_state: GameState, valid_actions: list):
        # Implement your strategy here
        action = valid_actions[0]
        params = {}
        return (action, params)
```

## CLI Commands

### `bank play`

Start an interactive game.

Options:
- `--players, -p`: Number of players (default: 2)
- `--human, -h`: Number of human players (default: 1)
- `--random, -r`: Number of random AI players (default: 0)
- `--rule-based, -rb`: Number of rule-based AI players (default: 0)
- `--seed, -s`: Random seed for reproducibility

### `bank demo`

Run a demonstration game with AI agents.

### `bank-train`

Train a DQN agent.

Options:
- `--episodes, -e`: Number of training episodes (default: 1000)
- `--players, -p`: Number of players (default: 2)
- `--save-path, -s`: Path to save the trained model
- `--load-path, -l`: Path to load an existing model

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bank --cov-report=html

# Run specific test file
pytest tests/game/test_engine.py
```

### Code Formatting

```bash
# Format code with black
black bank/ tests/

# Check code style with flake8
flake8 bank/ tests/

# Type checking with mypy
mypy bank/
```

## Configuration

You can customize game settings using a JSON configuration file:

```bash
cp config.example.json config.json
# Edit config.json with your settings
```

See `config.example.json` for available options.

## Architecture

### Game Engine

The game engine (`bank.game.engine.BankGame`) manages:
- Game state and rules
- Turn management
- Action validation
- Win conditions

### Agents

All agents inherit from `BaseAgent` and implement:
- `select_action()`: Choose an action given game state
- Lifecycle callbacks: `on_game_start()`, `on_turn_start()`, etc.

### Training Environment

The `BankEnv` class wraps the game as a Gymnasium environment, enabling:
- Standard RL training loops
- Integration with libraries like Stable-Baselines3
- Custom reward shaping

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [ ] Implement complete BANK! game rules
- [ ] Add more agent types (Monte Carlo, PPO, etc.)
- [ ] Create a web-based UI
- [ ] Add multiplayer network support
- [ ] Tournament mode for agent evaluation
- [ ] Save/load game states

## Contact

For questions or suggestions, please open an issue on GitHub.
