"""Test script to analyze tie frequency and behavior of LeaderPlusN agents in BANK! tournament play.

This script runs a large number of games with only LeaderPlusN agents and reports win/tie statistics.
"""

import collections

from bank.agents.advanced_agents import (
    LeaderPlusFiveAgent,
    LeaderPlusFourAgent,
    LeaderPlusOneAgent,
    LeaderPlusSevenAgent,
    LeaderPlusSixAgent,
    LeaderPlusThreeAgent,
    LeaderPlusTwoAgent,
)
from bank.game.engine import BankGame

AGENT_CLASSES = [
    LeaderPlusOneAgent,
    LeaderPlusTwoAgent,
    LeaderPlusThreeAgent,
    LeaderPlusFourAgent,
    LeaderPlusFiveAgent,
    LeaderPlusSixAgent,
    LeaderPlusSevenAgent,
]

NUM_GAMES = 1000
NUM_ROUNDS = 20
NUM_PLAYERS = 4


def run_tournament(num_games=NUM_GAMES, num_rounds=NUM_ROUNDS, agent_classes=AGENT_CLASSES):
    win_counts = collections.Counter()
    tie_counts = collections.Counter()
    all_ties = 0
    for game_idx in range(num_games):
        agents = [cls(i) for i, cls in enumerate(agent_classes[:NUM_PLAYERS])]
        engine = BankGame(num_players=len(agents), agents=agents, total_rounds=num_rounds)
        state = engine.play_game()
        # Find all players with the highest score
        scores = [p.score for p in state.players]
        max_score = max(scores)
        winners = [p.player_id for p in state.players if p.score == max_score]
        if len(winners) > 1:
            all_ties += 1
            for w in winners:
                tie_counts[w] += 1
        for w in winners:
            win_counts[w] += 1
    return win_counts, tie_counts, all_ties


def main():
    win_counts, tie_counts, all_ties = run_tournament()
    print("\n=== LeaderPlusN Tournament Analysis ===")
    print(f"Games: {NUM_GAMES} | Rounds: {NUM_ROUNDS} | Players: {NUM_PLAYERS}")
    print(f"Total ties: {all_ties} ({all_ties / NUM_GAMES:.1%})")
    print("\nWin counts:")
    for pid, count in sorted(win_counts.items()):
        print(f"  Agent {pid}: {count} wins ({count / NUM_GAMES:.1%})")
    print("\nTie counts (number of times each agent was in a tie):")
    for pid, count in sorted(tie_counts.items()):
        print(f"  Agent {pid}: {count} ties ({count / NUM_GAMES:.1%})")


if __name__ == "__main__":
    main()
