"""Tournament script for BANK! threshold and advanced agents.

Runs a 1000-game tournament (20 rounds each) for all advanced threshold agents and selected others.
Collects stats on wins, ties, and losses for each agent.
"""

import random
from collections import Counter, defaultdict

from bank.agents.advanced_agents import (
    LeaderOnlyAgent,
    LeaderPlusOneAgent,
    LeechAgent,
    RankBasedAgent,
)
from bank.agents.rule_based import AggressiveAgent, ConservativeAgent, SmartAgent
from bank.agents.threshold_agents import (
    threshold_300_agent,
    threshold_350_agent,
    threshold_400_agent,
    threshold_450_agent,
    threshold_500_agent,
)
from bank.game.engine import BankGame

AGENT_FACTORIES = [
    ("Threshold-300", threshold_300_agent),
    ("Threshold-350", threshold_350_agent),
    ("Threshold-400", threshold_400_agent),
    ("Threshold-450", threshold_450_agent),
    ("Threshold-500", threshold_500_agent),
    ("LeaderOnly", LeaderOnlyAgent),
    ("LeaderPlusOne", LeaderPlusOneAgent),
    ("Leech", LeechAgent),
    ("RankBased", RankBasedAgent),
    ("Smart", SmartAgent),
    ("Aggressive", AggressiveAgent),
    ("Conservative", ConservativeAgent),
]

NUM_GAMES = 1000
ROUNDS = 20

results = defaultdict(lambda: Counter({"win": 0, "tie": 0, "loss": 0}))

for i, (name, factory) in enumerate(AGENT_FACTORIES):
    print(f"\nEvaluating {name} agent...")
    for game_idx in range(NUM_GAMES):
        # Each agent plays against 3 random others (no duplicates)
        others = [f for j, f in enumerate(AGENT_FACTORIES) if j != i]
        opponents = random.sample(others, 3)
        agents = [factory(0)] + [op(1 + k) for k, op in enumerate(opponents)]
        agent_names = [name] + [n for n, _ in random.sample(others, 3)]
        game = BankGame(num_players=4, agents=agents, total_rounds=ROUNDS, rng=random.Random(game_idx))
        game.play_game()
        winner = game.state.winner
        my_score = game.state.players[0].score
        scores = [p.score for p in game.state.players]
        max_score = max(scores)
        if my_score == max_score:
            if scores.count(max_score) > 1:
                results[name]["tie"] += 1
            else:
                results[name]["win"] += 1
        else:
            results[name]["loss"] += 1
    print(f"{name}: {results[name]['win']} wins, {results[name]['tie']} ties, {results[name]['loss']} losses")

print("\n--- TOURNAMENT SUMMARY ---")
for name, stats in results.items():
    total = stats["win"] + stats["tie"] + stats["loss"]
    win_pct = 100 * stats["win"] / total
    tie_pct = 100 * stats["tie"] / total
    loss_pct = 100 * stats["loss"] / total
    print(
        f"{name:15}: {stats['win']:4} wins, {stats['tie']:4} ties, {stats['loss']:4} losses | Win%: {win_pct:.1f}  Tie%: {tie_pct:.1f}  Loss%: {loss_pct:.1f}"
    )
