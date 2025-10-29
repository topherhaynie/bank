Project plan for BANK! (phased roadmap)

Purpose
-------
This document records a phased plan for implementing the BANK! dice game, agent APIs, and RL training pipeline. It maps high-level phases to concrete tasks, expected deliverables, and testing/verification steps so future contributors and coding agents can pick up work and update status.

Phases & tasks
--------------

Phase 1 — Build the game engine (priority: high)
- Goal: Implement a correct, well-tested deterministic engine for the dice-based BANK! rules.
- Status: In Progress (2/4 tasks complete)
- Tasks & deliverables:
  1. ✅ **COMPLETE** `GameState` dataclasses: `bank/game/state.py` — typed models for game, round, and player state plus `to_dict`/`from_dict` serialization. Includes `PlayerState`, `RoundState`, and `GameState` with full serialization support and helper methods. Comprehensive test suite with 30 tests and 100% coverage in `tests/game/test_state.py`.
  2. ✅ **COMPLETE** Roll & bank mechanics: `bank/game/engine.py` — Complete implementation of 2d6 roll logic, bank accumulation, special first-3-roll rules for sevens (adds 70) and doubles (adds sum), post-3-roll rules (seven ends round, doubles double bank), player banking, round management, and deterministic RNG support. Refactored comprehensive test suite split across 5 files for better organization: `test_engine.py` (13 integration tests), `test_engine_initialization.py` (8 tests), `test_engine_rounds.py` (4 tests), `test_engine_dice.py` (2 tests), `test_engine_banking.py` (10 tests). Total: 37 tests with 90% coverage on engine.py.
  3. Decision polling loop: engine-level polling loop that notifies active players after each bank change and collects `bank`/`pass` responses (serializable, deterministic tie-breakers).
  4. Unit tests: Additional engine tests as needed for edge cases discovered during integration.

Phase 2 — Agent API & baseline agents (priority: high)
- Goal: Define and implement a stable agent interface and basic agents for testing and demos.
- Status: Not Started (0/4 tasks complete)
- Tasks & deliverables:
  1. Agent base API: `bank/agents/base.py` — `Agent` abstract class with `act(observation)` and `reset()`.
  2. Observation & action schema doc and types in `docs/`.
  3. Baseline agents: `bank/agents/random_agent.py`, `bank/agents/rule_based.py`.
  4. Agent tests: `tests/agents/test_agents.py` to validate integration with the engine.

Phase 3 — CLI & examples (priority: medium)
- Goal: Make the game playable locally and provide examples for inspection and tournaments.
- Status: Not Started (0/3 tasks complete)
- Tasks & deliverables:
  1. CLI runner: `bank/cli/game_runner.py` and `bank/cli/main.py` — interactive play, timeouts for human input, and match configuration.
  2. Examples: `examples/inspect_game.py`, `examples/simple_agent.py`, `examples/tournament.py`.
  3. Replay/inspection helpers for saving/loading game logs.

Phase 4 — Training environment & DQN (priority: medium)
- Goal: Provide a Gym-like environment wrapper and DQN training harness for learning agents.
- Status: Not Started (0/3 tasks complete)
- Tasks & deliverables:
  1. Environment wrapper: `bank/training/environment.py` — `reset()`, `step()`, observation flattening, action mask support, and episode termination semantics.
  2. DQN agent: `bank/training/dqn_agent.py` — basic DQN with replay buffer and epsilon-greedy policy.
  3. Training script: `bank/training/train.py` and `config.example.json` — checkpointing, evaluation, and logging.

Phase 5 — Testing, CI & quality (priority: high)
- Goal: Ensure correctness, maintainability, and reproducible experiments.
- Status: Not Started (0/3 tasks complete)
- Tasks & deliverables:
  1. Unit & integration tests for engine, agents, and training code (expand `tests/`).
  2. Linting and type checks (e.g., `ruff`, `mypy`) configured in the project.
  3. CI config (GitHub Actions) to run tests and linters on PRs.

Phase 6 — Evaluation & improvements (priority: low)
- Goal: Add tools for model comparison, tournaments, and experiment tracking.
- Status: Not Started (0/2 tasks complete)
- Tasks & deliverables:
  1. Tournament scripts, evaluation harness, and model comparison tooling.
  2. Optional integration with experiment tracking (Weights & Biases) for larger experiments.

Cross-cutting concerns
----------------------
- Determinism: All RNG usage must accept a seed or RNG object for reproducible tests and training.
- Observability: Provide structured logs and replay files (`to_dict` snapshots) to reproduce matches exactly.
- Backwards compatibility: Keep observation/action shapes versioned; update docs on changes.
- Minimal API surface: Keep engine and agent interfaces small and stable to reduce downstream breakage.

Testing & verification strategy
------------------------------
- Write unit tests first for each engine change (TDD approach encouraged).
- For ML code, write small smoke tests that run a few training iterations to ensure code paths execute.
- Use deterministic seeds in tests and CI.

How to update this plan
-----------------------
- When you start a task, update the project todo list (root-level) and set that task to `in-progress`.
- When you finish a task, mark it `completed` and add any newly discovered follow-ups.
- Keep this `docs/PROJECT_PLAN.md` as the canonical roadmap; break big tasks into smaller subtasks in the todo list as needed.

Immediate next steps (recommended)
---------------------------------
1. ✅ **COMPLETE** Implement `GameState` dataclasses and add basic unit tests for serialization.
2. ✅ **COMPLETE** Implement roll/bank logic and add tests for the first-3-roll exceptions, doubles, and sevens (Phase 1 Task 2).
3. **NEXT** Implement the polling decision loop and a simple random/pass agent to validate integration (Phase 1 Task 3).

Progress log
------------
- 2025-10-29: Completed Phase 1 Task 1 - Implemented `PlayerState`, `RoundState`, and `GameState` dataclasses with full serialization support. Created comprehensive test suite (30 tests, 100% coverage). Ready to begin Phase 1 Task 2.
- 2025-10-29: Completed Phase 1 Task 2 - Implemented complete dice rolling and banking mechanics in `bank/game/engine.py`. All BANK! game rules properly implemented: normal rolls add sum, sevens in first 3 rolls add 70, sevens after first 3 end round, doubles in first 3 add sum, doubles after first 3 double the bank. Player banking, round management, and game end conditions fully functional. Refactored test suite from single large file into 5 focused test modules for better organization and maintainability. All 67 tests passing (37 engine tests + 30 state tests) with 90% engine coverage.
