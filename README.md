# BANK! �

A modular Python game environment for the dice game BANK! with support for rule-based agents, AI training (DQN), and CLI gameplay.

## Features

- 🎯 **Game Engine**: Complete BANK! dice game implementation with state management
- 🤖 **Agent Support**: 
  - Rule-based agents (Random, Threshold, Conservative, Aggressive, Smart, Adaptive)
  - Deep Q-Network (DQN) reinforcement learning agents (in development)
  - Easy-to-extend base agent interface
- 🖥️ **CLI Interface**: Interactive command-line gameplay with human and AI players
- 🧠 **Training Framework**: Gymnasium-compatible environment for RL training (in development)
- 🧪 **Testing**: Comprehensive test suite with 114 tests and 89% coverage

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
# Play as a human against AI agents
bank play --players 3 --human 1 --smart 1 --aggressive 1

# Watch AI agents play against each other
bank demo

# Run a tournament with statistics
bank tournament --games 100
```

### Create Custom Agents

```python
from bank.agents.base import Agent, Action, Observation

class MyCustomAgent:
    def __init__(self, player_id: int, name: str):
        self.player_id = player_id
        self.name = name
    
    def act(self, observation: Observation) -> Action:
        """Decide whether to 'bank' or 'pass' based on observation."""
        # Implement your strategy here
        if observation["current_bank"] >= 80:
            return "bank"
        return "pass"
    
    def reset(self) -> None:
        """Reset agent state for a new game."""
        pass
```

## CLI Commands

### `bank play`

Start an interactive game with human and/or AI players.

Options:
- `--players, -p`: Number of players (2-6, default: 4)
- `--human, -h`: Number of human players (default: 1)
- `--random`: Number of random AI players
- `--threshold <N>`: Number of threshold-based AI players
- `--conservative`: Number of conservative AI players
- `--aggressive`: Number of aggressive AI players
- `--smart`: Number of smart AI players
- `--adaptive`: Number of adaptive AI players
- `--rounds, -r`: Number of rounds to play (default: 5)
- `--seed, -s`: Random seed for reproducibility
- `--timeout, -t`: Decision timeout in seconds for humans (default: 30)
- `--delay, -d`: Delay between AI actions in seconds (default: 1.0)

### `bank demo`

Run a demonstration game with 4 AI agents.

Options:
- `--rounds, -r`: Number of rounds (default: 3)
- `--delay, -d`: Delay between actions in seconds (default: 1.0)
- `--seed, -s`: Random seed

### `bank tournament`

Run a tournament with multiple games and collect statistics.

Options:
- `--games, -g`: Number of games to play (default: 10)
- `--players, -p`: Number of players per game (default: 4)
- `--rounds, -r`: Number of rounds per game (default: 5)
- `--seed, -s`: Random seed

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
- Dice rolling (2d6) with special rules for doubles and sevens
- Banking mechanics and round progression
- Player state tracking and decision polling
- Game flow and win conditions

### Agents

All agents implement the `Agent` protocol:
- `act(observation: Observation) -> Action`: Choose "bank" or "pass"
- `reset() -> None`: Reset state for a new game

The `Observation` TypedDict provides complete game state information:
- Round number, roll count, current bank value
- Last dice roll, active players
- Player scores and banking status

### Training Environment (In Development)

The `BankEnv` class will wrap the game as a Gymnasium environment, enabling:
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

- [x] Implement complete BANK! dice game rules
- [x] Add multiple agent types (Random, Threshold, Conservative, Aggressive, Smart, Adaptive)
- [x] CLI interface with human play and tournaments
- [x] Comprehensive test suite (114 tests, 89% coverage)
- [ ] DQN reinforcement learning agent
- [ ] Advanced agent types (Monte Carlo, PPO, etc.)
- [ ] Web-based UI
- [ ] Multiplayer network support
- [ ] Enhanced tournament and evaluation tools

## Implementation Status

**Current State:**
- ✅ Complete dice game implementation
- ✅ Full game engine with all BANK! rules
- ✅ Six rule-based agent strategies
- ✅ Interactive CLI with human and AI players
- ✅ Tournament mode with statistics
- ✅ Programmatic examples for custom agents
- ✅ Comprehensive test coverage
- ⏳ DQN training framework (Phase 4)
- ⏳ Replay/inspection helpers (Phase 3 Task 3)

The project is production-ready for playing BANK! and developing custom rule-based agents. The RL training framework is the next major development phase.

## Contact

For questions or suggestions, please open an issue on GitHub.
