# Code Conventions and Patterns

This document describes the coding conventions, patterns, and design decisions used in the BANK! project to help contributors understand the codebase structure.

## Table of Contents
- [Project Structure](#project-structure)
- [Type Hints and Typing](#type-hints-and-typing)
- [Data Classes and State Management](#data-classes-and-state-management)
- [Agent Interface](#agent-interface)
- [Testing Conventions](#testing-conventions)
- [Import Patterns](#import-patterns)
- [Naming Conventions](#naming-conventions)
- [Error Handling](#error-handling)
- [Determinism and Reproducibility](#determinism-and-reproducibility)
- [Documentation Standards](#documentation-standards)
- [Common Pitfalls](#common-pitfalls)
- [Summary Checklist](#summary-checklist)
- [Engine API Reference](#engine-api-reference)
- [Working with Agents](#working-with-agents)

## Project Structure

```
bank/
├── agents/          # Agent implementations and base classes
├── cli/             # Command-line interface and human player
├── game/            # Core game engine and state
├── training/        # RL training code and environments
└── utils/           # Shared utilities and configuration

tests/
├── agents/          # Agent tests
├── game/            # Game engine tests (split by feature)
└── utils/           # Utility tests

docs/
├── ARCHITECTURE.md      # High-level design and flow
├── BASE_GAME_RULES.md  # Game rules reference
├── CONVENTIONS.md      # This file
└── PROJECT_PLAN.md     # Phased implementation plan
```

## Type Hints and Typing

### Python Version and Type Features

- **Target Python Version**: 3.10+
- **Modern Type Syntax**: Use `list[T]`, `dict[K, V]`, `tuple[T, ...]` instead of `List[T]`, `Dict[K, V]`, `Tuple[T, ...]`
- **Union Types**: Use `X | None` instead of `Optional[X]` or `Union[X, None]`
- **Forward References**: Use `from __future__ import annotations` to avoid string quotes in type hints

### Type Hint Patterns

```python
# Correct - modern syntax
def process_players(players: list[PlayerState]) -> dict[int, int]:
    return {p.player_id: p.score for p in players}

# Avoid - old syntax
from typing import List, Dict
def process_players(players: List[PlayerState]) -> Dict[int, int]:
    return {p.player_id: p.score for p in players}
```

### Action Type System

Actions in the dice game use `Literal` types for type safety:

```python
from typing import Literal

# Type alias for valid actions
Action = Literal["bank", "pass"]

# Usage in agent interface
def act(self, observation: Observation) -> Action:
    return "bank"  # Type checker validates this
```

### TYPE_CHECKING Pattern

For circular imports, use the TYPE_CHECKING guard:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank.agents.base import Agent, Observation, Action

# These types are only available for type checkers, not at runtime
```

## Data Classes and State Management

### Dataclass Usage

The project uses Python's `@dataclass` decorator for state classes:

```python
from dataclasses import dataclass, field

@dataclass
class PlayerState:
    player_id: int
    name: str
    score: int = 0
    has_banked_this_round: bool = False
```

**Key Points:**
- State classes (`PlayerState`, `RoundState`, `GameState`) are dataclasses
- Use `field(default_factory=...)` for mutable defaults (lists, dicts, sets)
- Provide `to_dict()` and `from_dict()` methods for serialization

### Game Initialization Pattern

The `BankGame` engine uses a private `_initialize_game()` method:

```python
class BankGame:
    def __init__(self, num_players: int = 2, ...):
        # Validation
        if num_players < MIN_PLAYERS:
            raise ValueError(...)
        
        # Initialization
        self.rng = rng or random.Random()
        self.state = self._initialize_game(player_names, total_rounds)
        self.agents = agents
        
    def _initialize_game(self, player_names: list[str], total_rounds: int) -> GameState:
        """Private helper to create initial game state."""
        players = [PlayerState(i, name) for i, name in enumerate(player_names)]
        return GameState(players=players, total_rounds=total_rounds)
```

**Important:**
- `GameState` is instantiated directly, not through a `create()` class method
- `_initialize_game()` is private and only called during `__init__`
- Reset operations also use `_initialize_game()`

### State Access Patterns

```python
# Accessing current round
if self.state.current_round:
    bank = self.state.current_round.current_bank
    
# Getting a player
player = self.state.get_player(player_id)
if player:
    score = player.score

# Checking active players
active = self.state.get_active_players()
```

## Agent Interface

### Two Agent Interfaces

The codebase maintains two agent interfaces:

1. **`Agent`** - For the dice-based BANK! game (current implementation)
2. **`BaseAgent`** - Legacy interface for card-based game (backward compatibility)

### Agent Implementation Pattern

```python
from bank.agents.base import Action, Agent, Observation

class MyAgent(Agent):
    """Agent that implements some strategy."""
    
    def __init__(self, player_id: int, threshold: int = 50, name: str | None = None):
        super().__init__(player_id, name)
        self.threshold = threshold
    
    def act(self, observation: Observation) -> Action:
        """Make a decision based on observation."""
        if observation["can_bank"] and observation["current_bank"] >= self.threshold:
            return "bank"
        return "pass"
    
    def reset(self) -> None:
        """Reset agent state (optional override)."""
        # Reset any internal state here
        pass
```

### Observation Structure

The `Observation` TypedDict provides all game state to agents:

```python
{
    "round_number": 3,           # Current round (1-based)
    "roll_count": 5,             # Rolls in current round (1-based)
    "current_bank": 25,          # Points in the bank
    "last_roll": (4, 6),         # Most recent dice roll
    "active_player_ids": {0, 1}, # Players still active this round
    "player_id": 0,              # This player's ID
    "player_score": 15,          # This player's total score
    "can_bank": True,            # Can this player bank?
    "all_player_scores": {0: 15, 1: 20}  # All player scores
}
```

### Polling Modes

The engine supports two polling modes via `deterministic_polling` parameter:

```python
# Simultaneous polling (default) - realistic gameplay
game = BankGame(num_players=2, agents=agents, deterministic_polling=False)

# Deterministic polling - for testing
game = BankGame(num_players=2, agents=agents, deterministic_polling=True)
```

**Simultaneous Mode (Default):**
- All agents receive observations simultaneously
- Decisions collected before any are processed
- Agents don't see each other's choices
- Better for training and realistic gameplay

**Deterministic Mode:**
- Agents polled sequentially in sorted player ID order
- Each decision processed immediately
- Useful for reproducible test scenarios

## Testing Conventions

### Test Organization

Tests are organized by feature area:

```
tests/game/
├── test_state.py              # State dataclass tests
├── test_engine.py             # Core engine integration tests
├── test_engine_initialization.py  # Initialization tests
├── test_engine_rounds.py      # Round management tests
├── test_engine_dice.py        # Dice rolling tests
├── test_engine_banking.py     # Banking mechanics tests
└── test_engine_polling.py     # Agent polling tests
```

### Test Class Organization

```python
class TestFeatureGroup:
    """Test a specific feature or component."""
    
    def test_specific_behavior(self):
        """Test one specific behavior or edge case."""
        # Arrange
        game = BankGame(num_players=2)
        
        # Act
        result = game.some_action()
        
        # Assert
        assert result == expected_value
```

### Test Naming

- Test files: `test_<module>.py` or `test_<module>_<feature>.py`
- Test classes: `Test<FeatureGroup>`
- Test methods: `test_<what_it_tests>` with descriptive names

### Test Agents

Use test agents from `bank.agents.test_agents` for testing:

```python
from bank.agents.test_agents import AlwaysBankAgent, AlwaysPassAgent, ThresholdAgent

# Simple deterministic behavior
agents = [AlwaysPassAgent(0), AlwaysBankAgent(1)]

# Threshold-based behavior
agents = [ThresholdAgent(0, threshold=50), ThresholdAgent(1, threshold=100)]
```

### Deterministic Testing

For reproducible tests, use seeded RNG and deterministic polling:

```python
import random

# Seeded game for deterministic dice rolls
rng = random.Random(42)
game = BankGame(num_players=2, rng=rng)

# Deterministic polling for ordered agent decisions
game = BankGame(num_players=2, agents=agents, deterministic_polling=True)

# Mock dice rolls for specific test scenarios
game.roll_dice = lambda: (3, 4)  # Always roll 3 and 4
```

## Import Patterns

### Standard Import Order

Follow this import order (enforced by linters):

```python
# 1. Future imports
from __future__ import annotations

# 2. Standard library
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal, TypedDict

# 3. Local imports
from bank.game.state import GameState, PlayerState

# 4. TYPE_CHECKING imports (for type hints only)
if TYPE_CHECKING:
    from bank.agents.base import Agent, Observation
```

### Avoiding Circular Imports

Use TYPE_CHECKING guard for circular dependencies:

```python
# In engine.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank.agents.base import Agent

# Then use quotes or annotations for type hints
def poll_decisions(self) -> list[int]:
    agent: Agent = self.agents[0]  # Works with annotations import
```

### Local Imports in Methods

For runtime-only imports that would cause circular dependencies:

```python
def create_observation(self, player_id: int) -> Observation:
    # Import here to avoid circular dependency at module level
    from bank.agents.base import Observation
    
    return Observation(
        round_number=self.state.round_number,
        # ...
    )
```

## Naming Conventions

### General Rules

- **Modules**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `lowercase_with_underscores()`
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES`
- **Private methods**: `_leading_underscore()`
- **Type aliases**: `PascalCase` (e.g., `Action = Literal[...]`)

### Common Variable Names

```python
# Player identification
player_id: int           # Integer ID (0, 1, 2, ...)
player: PlayerState      # Player state object

# Game state
state: GameState         # Full game state
round_state: RoundState  # Current round state

# Agents
agent: Agent             # Single agent instance
agents: list[Agent]      # List of all agents

# Observations and actions
observation: Observation # Agent observation dict
action: Action          # Agent action ("bank" or "pass")

# Dice
roll: tuple[int, int]   # Dice roll result
last_roll: tuple[int, int] | None  # Previous roll or None
```

### Method Naming Patterns

```python
# Getters
def get_player(self, player_id: int) -> PlayerState | None:
    """Get a player by ID."""

# Boolean checks
def is_round_over(self) -> bool:
    """Check if round is over."""

def can_bank(self, player_id: int) -> bool:
    """Check if player can bank."""

# State modifications
def player_banks(self, player_id: int) -> bool:
    """Process a player banking."""

def start_new_round(self) -> None:
    """Start a new round."""

# Private helpers
def _initialize_game(self, ...) -> GameState:
    """Private initialization helper."""

def _poll_simultaneous(self, ...) -> list[int]:
    """Private polling implementation."""
```

## Error Handling

### Validation Pattern

```python
def __init__(self, num_players: int = 2, ...):
    # Validate parameters
    if num_players < MIN_PLAYERS:
        msg = f"Must have at least {MIN_PLAYERS} players"
        raise ValueError(msg)
    
    if agents is not None and len(agents) != num_players:
        msg = "Number of agents must match number of players"
        raise ValueError(msg)
    
    # Initialize after validation
    self.state = ...
```

### Runtime Checks

```python
def create_observation(self, player_id: int) -> Observation:
    if not self.state.current_round:
        msg = "Cannot create observation: no active round"
        raise RuntimeError(msg)
    
    player = self.state.get_player(player_id)
    if not player:
        msg = f"Invalid player_id: {player_id}"
        raise ValueError(msg)
    
    # Proceed with valid state
    return Observation(...)
```

## Determinism and Reproducibility

### RNG Management

Always accept optional `rng` parameter for deterministic behavior:

```python
def __init__(self, rng: random.Random | None = None):
    self.rng = rng or random.Random()

# Usage
rng = random.Random(42)  # Seeded
game = BankGame(num_players=2, rng=rng)
```

### Polling Determinism

Use `deterministic_polling=True` for reproducible agent testing:

```python
# Deterministic for tests
game = BankGame(agents=agents, deterministic_polling=True)
# Agents polled in sorted order: 0, 1, 2, ...

# Simultaneous for realistic gameplay
game = BankGame(agents=agents, deterministic_polling=False)
# All agents polled together, decisions processed in sorted order
```

### Testing Determinism

Always use seeds in tests:

```python
def test_dice_rolls():
    """Test should be reproducible."""
    rng = random.Random(12345)
    game = BankGame(num_players=2, rng=rng)
    
    # Test will produce same results every time
    assert game.roll_dice() == (expected_roll)
```

## Documentation Standards

### Docstring Format

Use Google-style docstrings:

```python
def player_banks(self, player_id: int) -> bool:
    """Process a player banking action.

    Args:
        player_id: ID of the player who wants to bank

    Returns:
        True if banking was successful, False otherwise

    Raises:
        ValueError: If player_id is invalid

    """
    # Implementation
```

### Comments

- Use comments to explain **why**, not **what**
- Document edge cases and special behaviors
- Reference game rules when implementing them

```python
# First 3 rolls: seven adds 70 points (rule exception)
if self.state.current_round.is_first_three_rolls():
    if roll_sum == SEVEN_VALUE:
        self.state.current_round.current_bank += SEVEN_BONUS_POINTS
```

## Common Pitfalls

### Don't Call Non-Existent Methods

```python
# ❌ Wrong - GameState has no create() method
self.state = GameState.create(num_players, player_names, total_rounds)

# ✅ Correct - Use _initialize_game() helper
self.state = self._initialize_game(player_names, total_rounds)
```

### Don't Use Old-Style Type Hints

```python
# ❌ Wrong - requires import from typing
def process(players: List[PlayerState]) -> Dict[int, int]:
    pass

# ✅ Correct - modern Python 3.10+ syntax
def process(players: list[PlayerState]) -> dict[int, int]:
    pass
```

### Don't Access State Without Checking

```python
# ❌ Wrong - might be None
bank = self.state.current_round.current_bank

# ✅ Correct - check first
if self.state.current_round:
    bank = self.state.current_round.current_bank
```

### Don't Forget TYPE_CHECKING for Circular Imports

```python
# ❌ Wrong - causes circular import at runtime
from bank.agents.base import Agent

# ✅ Correct - import only for type checking
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bank.agents.base import Agent
```

## Summary Checklist

When adding new code, ensure:

- ✅ Using Python 3.10+ type syntax (no `List`, `Dict`, `Optional`)
- ✅ Using `from __future__ import annotations` when needed
- ✅ Using TYPE_CHECKING guard for circular imports
- ✅ Following import order: future, stdlib, local, TYPE_CHECKING
- ✅ Providing Google-style docstrings for public APIs
- ✅ Supporting determinism via `rng` parameter where applicable
- ✅ Validating inputs and raising clear error messages
- ✅ Writing tests with descriptive names
- ✅ Checking state objects for None before accessing attributes
- ✅ Using `Action = Literal["bank", "pass"]` for action types

## Engine API Reference

### Key Methods and Attributes

Understanding how to use the game engine correctly:

#### GameState Attributes (Not Methods!)

```python
# ❌ Wrong - these are attributes, not methods
if game.state.is_game_over():  # AttributeError!
    pass

# ✅ Correct - access as attributes
if game.state.game_over:  # Boolean attribute
    pass

# Common GameState attributes:
game.state.game_over          # bool - whether game has ended
game.state.winner             # int | None - winning player ID
game.state.total_rounds       # int - total rounds to play
game.state.players            # list[PlayerState] - all players
game.state.current_round      # RoundState | None - current round state
```

#### Accessing Round Information

```python
# ❌ Wrong - GameState has no round_number attribute
round_num = game.state.round_number  # AttributeError!

# ✅ Correct - round_number is in current_round
if game.state.current_round:
    round_num = game.state.current_round.round_number
    
# Common RoundState attributes (when current_round is not None):
game.state.current_round.round_number      # int - 1-based round number
game.state.current_round.roll_count        # int - rolls in this round
game.state.current_round.current_bank      # int - points in bank
game.state.current_round.last_roll         # tuple[int, int] | None
game.state.current_round.active_player_ids # set[int] - players not banked
```

#### Engine Methods for Game Control

```python
# High-level game control
game.play_game()      # Play complete game to completion (requires agents)
game.play_round()     # Play one complete round (requires agents)

# Low-level round control
game.start_new_round()       # Start a new round
game.roll_dice()             # Roll dice, returns (die1, die2)
game.process_roll()          # Roll dice and update bank
game.poll_decisions()        # Poll agents for banking decisions
game.player_banks(player_id) # Process a player banking

# State queries
game.is_round_over()         # Check if current round is complete
game.is_game_over()          # Check if game has ended (wrapper for state.game_over)
game.get_winner()            # Get winning PlayerState or None
game.get_active_players()    # Get list of non-banked players

# State management
game.reset(seed)             # Reset game to initial state
game.get_state()             # Get current GameState
```

#### When to Use play_game() vs Manual Control

```python
# ✅ Use play_game() for: full automated games, testing, tournaments
agents = [RandomAgent(0), ThresholdAgent(1, threshold=50)]
game = BankGame(num_players=2, agents=agents, total_rounds=10)
game.play_game()  # Runs complete game automatically
winner = game.get_winner()

# ✅ Use manual control for: step-by-step execution, custom logic, debugging
game = BankGame(num_players=2, agents=agents)
game.start_new_round()
roll = game.roll_dice()  # Returns dice values
game.process_roll()      # Updates bank based on roll
game.poll_decisions()    # Asks agents to bank/pass
# Repeat until game.is_round_over()
```

#### Agent Requirements

```python
# ❌ Wrong - play_game() requires agents
game = BankGame(num_players=2)
game.play_game()  # RuntimeError: Cannot play game without agents

# ✅ Correct - provide agents
agents = [ThresholdAgent(0, threshold=50), ThresholdAgent(1, threshold=60)]
game = BankGame(num_players=2, agents=agents)
game.play_game()  # Works!

# ✅ Correct - manual control works without agents (for custom logic)
game = BankGame(num_players=2)
game.start_new_round()
roll = game.roll_dice()
# Custom banking logic here
```

#### Deterministic Game Execution

```python
# For reproducible results, seed both RNG and agents
import random

rng = random.Random(42)
agents = [
    RandomAgent(0, seed=100),  # Agent's RNG
    RandomAgent(1, seed=200),  # Agent's RNG
]
game = BankGame(
    num_players=2,
    agents=agents,
    rng=rng,  # Game's RNG for dice
    deterministic_polling=True,  # Optional: sequential polling
)
game.play_game()
# Results are fully reproducible
```

## Working with Agents

### Agent Interface Requirements

```python
# All agents must:
# 1. Inherit from Agent base class
# 2. Implement act(observation) -> Action
# 3. Accept player_id in __init__
# 4. (Optional) Implement reset() for stateful agents

from bank.agents.base import Agent, Action, Observation

class MyAgent(Agent):
    def __init__(self, player_id: int, name: str | None = None):
        super().__init__(player_id, name)
        # Your initialization here
    
    def act(self, observation: Observation) -> Action:
        # Must return "bank" or "pass"
        if observation["can_bank"] and observation["current_bank"] >= 50:
            return "bank"
        return "pass"
    
    def reset(self) -> None:
        # Optional: reset internal state
        pass
```

### Observation Structure Access

```python
# Observation is a TypedDict with these fields:
obs = agent.act(observation)

# Always check can_bank before banking
if observation["can_bank"]:
    # Can make banking decision
    pass

# Access game context
round_num = observation["round_number"]      # 1-based
roll_count = observation["roll_count"]       # 1-based
bank = observation["current_bank"]           # Current points
last_roll = observation["last_roll"]         # (die1, die2) or None
active = observation["active_player_ids"]    # set[int]
my_score = observation["player_score"]       # My total score
all_scores = observation["all_player_scores"] # dict[int, int]
```

## Questions or Updates?

If you find patterns not covered here or conventions that should be updated, please:
1. Update this document
2. Ensure existing code follows the conventions
3. Update PROJECT_PLAN.md if it affects implementation strategy

---

**Last Updated**: October 29, 2025 (Phase 2 completion - added Engine API reference section)
