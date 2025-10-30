Architecture for BANK! mini-application

Overview
--------
This document describes the high-level architecture for the BANK! project: components, responsibilities, and data flow. It's intended to guide implementation decisions, agent interfaces, and the training pipeline.

Top-level components
--------------------
- bank/game: Game engine and state model. Responsibilities:
  - Represent game state immutably where possible
  - Validate and apply actions, compute legal moves
  - Manage turn order, scoring, and game termination
  - Emit events or logs for replay/inspection

- bank/agents: Agent implementations and interfaces. Responsibilities:
  - Provide a standard Agent API (see Agent contract) for selecting actions given observations
  - Include simple agents (random, rule-based) and adapters for ML agents

- bank/cli: Command-line interface. Responsibilities:
  - Run matches with specified players (human or agents)
  - Configure match parameters (seed, players, verbose logging)
  - Provide human input handling and display

- bank/training: Training environment and algorithms. Responsibilities:
  - Provide an RL training loop (DQN) and environment wrapper
  - Convert game state into observations and action spaces for agents
  - Log training metrics and checkpoints

- utils: Shared utilities (config parsing, RNG seeding, helper functions)

Data flow
---------
1. CLI or training script requests a new Game from `bank.game.engine` with a config.
2. The Game initializes a `GameState` and registers players/agents.
3. On each turn, the Game queries the active agent with an Observation and ActionMask.
4. Agent returns an Action; the Game validates and applies it, updating GameState.
5. Repeat until terminal state. Game returns results (scores, winner(s), logs).

Agent contract (minimal)
------------------------
Agents implement a simple, predictable API to allow interchangeability between human, scripted, and ML players.

Current implementation:
- class Agent (Protocol):
  - def __init__(self, player_id: int, name: str)
  - def act(self, observation: Observation) -> Action
    - observation: TypedDict with game state (round_number, roll_count, current_bank, last_roll, active_player_ids, player_id, player_score, can_bank, all_player_scores)
    - returns: Action literal ("bank" or "pass")
  - def reset(self) -> None: (optional) called at start of new game

Observation & action design
---------------------------
- Observation is a TypedDict providing complete game state information in a structured, type-safe format.
- For ML agents, `bank.training.environment` will provide a flattened or tensorized observation.
- Actions are simple literals ("bank" or "pass") validated by the observation's `can_bank` field.

Testing and determinism
-----------------------
- All core game logic must be unit-tested (see `tests/game/test_engine.py`).
- Functions that rely on randomness should accept RNG or seed parameters to make tests deterministic.

Training pipeline
-----------------
- `bank.training.train` orchestrates episodes, batches transitions into replay buffers, and periodically evaluates saved checkpoints.
- Checkpointing and config-based runs are required: `config.example.json` should include trainer hyperparameters.

Extensions and interoperability
------------------------------
- Design the engine and agent interfaces to be minimal and stable. Keep observation/action formats versioned.
- Consider providing an OpenAI Gym-style wrapper for the environment to reuse RL tooling.

Notes
-----
- This document is intentionally implementation-agnostic. Specific data shapes and interfaces will be added to code docs and type hints in the source.
