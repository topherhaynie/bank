BANK! — Base game rules (dice variant)

Purpose
-------
This document records the canonical rules for BANK! as a dice-based party game. These rules replace earlier card-based assumptions. Use this as the authoritative source for implementing the engine, agents, and tests.

Game overview
-------------
- BANK! is a competitive dice game for 2+ players played over a fixed number of rounds (10, 15, or 20).
- Each round consists of repeated dice rolls that accumulate points into a shared "bank". Players may shout "bank" at any time to claim the current bank value and exit the round. Once a player banks, they score the bank amount and take no further actions for that round.
- Rounds end when either:
  - all players have banked, or
  - a seven (total of the two dice) is rolled (except during the first three rolls of the round; see special rules below).
- After a round ends, the bank resets to 0 and a new round begins. After the pre-set number of rounds, the player with the highest total score wins.

Turn & rolling model
---------------------
- Each roll uses two standard six-sided dice (2d6).
- The game normally proceeds in a turn-taking fashion (player A rolls, then B, etc.), but which player rolls is not important to the rules — any player (human or agent) may be the roller. The engine should allow configuration of roll ownership (round-robin, random, or agent-chosen) or let agents provide their own RNG for deciding roll outcomes in training/evaluation.

Bank accumulation rules
-----------------------
- After each roll, points are added to the global bank according to the following rules:
  - Normal roll (non-double, not seven): add the sum of the two dice to the bank.
  - Seven (sum == 7): ends the round immediately and resets the bank to 0, except:
    - During the first three rolls of the round (rolls 1..3), a seven does NOT end the round; instead it adds 70 points to the bank.
  - Doubles (both dice show same face): behavior depends on which roll of the round it is:
    - During the first three rolls (rolls 1..3): doubles add their total (same as a normal roll).
    - On rolls after the first three (rolls >=4): doubles do NOT add the dice total; instead they double the current bank (i.e., bank = bank * 2). The doubled bank is then subject to being banked by players or lost if a subsequent seven occurs.

Banking (player action)
-----------------------
- At any point (including immediately after a roll), any player may declare "bank". When a player banks:
  - They immediately add the current bank value to their personal score.
  - They are removed from further participation in the current round (they cannot roll or bank again until the next round).
  - The bank remains available for other players to bank until the round ends (i.e., multiple players may bank the same bank value if they do so before it changes or the round ends).

Round termination rules
----------------------
- A round ends when either all players have banked, or when a seven is rolled (subject to the first-3-roll exception). At round end:
  - If the round ended due to a roll of seven (outside the first 3 rolls), the bank is reset to 0 and no points are awarded for that round.
  - If the round ended because all players banked, proceed to the next round (bank resets to 0 after banking is processed).

Special cases & clarifications
-------------------------------
- First three rolls: rolls are counted per round (not per player). That means the first three rolls after the round starts — regardless of who rolled them — use the special seven/doubles rules described above.
- If multiple players decide to bank simultaneously (e.g., human console input vs agent), the engine should serialize banking attempts deterministically (timestamp order, player index order, or other stable tie-break) so results are reproducible in tests and training logs.
- If a player banks immediately after a doubles roll that doubled the bank, they receive the doubled amount.
- If a seven is rolled during the first three rolls, it adds 70 points (it does not end the round). If later a seven is rolled (roll >=4), the round ends immediately and the bank is lost.

Agent interaction model
-----------------------
- Because banking is asynchronous (players may bank at any time), the engine will use an explicit polling/decision loop each time the bank value changes to give remaining players the opportunity to respond.

- Suggested flow for each roll:
  1. Roller (player or agent) rolls 2d6 and engine updates the bank according to the rules above.
  2. The engine notifies all players who are still active in the round of the new observation (including current bank, roll index, recent roll result, and whether the round would terminate on a seven).
  3. The engine enters a short decision phase where it queries each non-banked player's agent code (or human input) for a decision: "bank" or "pass". To allow reactive behavior, the engine should collect responses in a loop — if any player banks during a decision pass, the engine should re-poll remaining players (because the bank value is still available and players might decide to bank in response).
  4. Once all active players either pass or the engine has no more change in banking decisions, play proceeds to the next roll (or the round terminates if conditions are met).

- To support human players in CLI mode, provide a configurable decision timeout and a deterministic fallback (default to pass) when no input is received. For training, agents should return responses immediately (synchronously) to avoid slowing training.

Observation API (suggested)
---------------------------
Each player should receive an observation dict (or typed object) each time a decision is requested. Suggested fields:
- round_index: int (1-based)
- roll_index: int (1-based within the round)
- bank: int (current bank value)
- last_roll: tuple(int die1, int die2) or None
- active_players: list of player ids still in the round (including the observing player)
- can_bank: bool (true if the observing player has not yet banked)

Agent action API (suggested)
---------------------------
- act(observation) -> Action
  - Action is one of: {"bank"}, {"pass"}, or optionally more complex structured responses (e.g., request to roll if the agent is configured as the roller).

Testing suggestions
-------------------
- Unit tests should cover:
  - Bank accumulation for normal rolls, doubles (early vs late), and seven behavior (early vs late).
  - Banking serialization: multiple players attempting to bank in the same decision phase.
  - Round termination on seven and when all players have banked.
  - Deterministic behavior with seeded RNG.

Training notes
--------------
- The environment should present a consistent observation space and a simple two-action action space (bank/pass) for RL agents.
- Because players can bank asynchronously, training episodes should treat each decision-phase as an opportunity for an agent to act (i.e., RL steps occur on decision events, not necessarily on rolls).
- For DQN, flatten the observation into a fixed-size vector; include features such as current bank, roll_index, player score, and number of active players. Provide an action mask so agents cannot bank if they've already banked this round.

Open design questions to decide before implementation
----------------------------------------------------
- Decision timeout for human players (and default behavior on timeout).
- Roll ownership policy (round-robin by player index vs free-for-all vs agent-chosen); impacts who is asked to roll and how RNG is sourced.
- Tie-break ordering when multiple banks arrive simultaneously (timestamp vs configured player order).

If these rules look correct, I'll update the engine design and tests to match them and implement the asynchronous polling decision loop for banking.
BANK! — Base game rules and implementation notes

Purpose
-------
This document records the rules, assumptions, and edge cases of the BANK! base card game as implemented in this repository. Use it to drive the engine's behavior and to write tests that assert correct play.

High-level summary
------------------
- BANK! is a turn-based card game for 2+ players.
- Each player has a hand of cards and interacts with shared central piles and personal stacks (specific names and mechanics to be detailed below).
- The game ends when a terminal condition is reached (e.g., deck exhaustion or a player empties their hand/stacks). The winner is determined by score or by meeting win conditions.

Assumptions for the initial implementation (MVP)
-----------------------------------------------
To keep the MVP focused and testable, we'll adopt these assumptions that can be relaxed later:

1. Players: support 2-4 players initially.
2. Deck: Standard numeric card deck — for the MVP represent cards as integers (e.g., 1..N). Concrete card identities and suits are unnecessary unless scoring requires it.
3. Turn order: Fixed clockwise turn order determined at game start.
4. Hidden information: Each player's hand is private. Public piles (e.g., discard) are fully visible.
5. Actions: On their turn, a player may play one action from a finite ActionSpace (draw, play to pile, discard, pass, special actions). The concrete action mapping will be defined in the engine API.
6. Legal moves: The engine must validate legality and reject illegal actions.
7. Randomness: Deck shuffling and agent randomness must be seedable via RNG objects.

Game state elements (engine should model these)
---------------------------------------------
- deck: draw pile
- discard_pile(s): central piles visible to all
- player_hands: private lists per player
- player_stacks: personal stacks that may be used for scoring or play
- scores: per-player numeric scores
- turn: index of active player and phase indicator (if multi-phase turns exist)

Important rules / behaviors to codify
-----------------------------------
- Drawing: If deck is empty, define behavior (reshuffle from discard or stop drawing). Document chosen approach.
- Play validation: Define card compatibility rules for playing onto a pile (e.g., must be same suit or next value); for MVP keep rules simple (e.g., any card may be played onto any pile) and add stricter rules later.
- Endgame & scoring: For MVP, simplest win condition: first player to empty their hand wins; tie-break by score. Later switch to point-based scoring.
- Special cards: Defer implementation of special cards and powers until base mechanics are verified.

Edge cases and tests to include
------------------------------
- Illegal action attempt by agent or malformed action payload — engine should raise an explicit exception and optionally penalize agent in training mode.
- Simultaneous terminal conditions (e.g., last-card play and deck exhaustion) — define deterministic tie-break rules.
- Consistency of observation: ensure private hand info is never exposed to other players' observations.

Next steps for rule refinement
-----------------------------
1. Map the concrete card set and actions used in the repo's existing code (search for card constants in `bank/game` and `bank/agents`).
2. Write unit tests that assert order of play, draw/discard mechanics, and sample legal move flows.
3. After tests pass, add more complex rules (special actions, multi-phase turns, scoring variants).

Implementation notes
--------------------
- Use small, clear data classes for `GameState`, `PlayerState`, and `Action` to make tests and serialization straightforward.
- Provide serialization helpers (`to_dict`, `from_dict`) for saving replays and for the training environment.
