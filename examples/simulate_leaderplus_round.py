"""Simulate a single round of BANK! with multiple LeaderPlusN agents, printing their wait counters and actions after each roll."""

import random

from bank.agents.advanced_agents import (
    LeaderPlusFourAgent,
    LeaderPlusOneAgent,
    LeaderPlusThreeAgent,
    LeaderPlusTwoAgent,
)


class DummyObservation(dict):
    pass


def simulate_leaderplus_round():
    agents = [
        LeaderPlusOneAgent(0),
        LeaderPlusTwoAgent(1),
        LeaderPlusThreeAgent(2),
        LeaderPlusFourAgent(3),
    ]
    scores = [0, 0, 0, 0]
    bank = 0
    roll_count = 0
    active = [True, True, True, True]
    wait_counters = [a._wait_counter for a in agents]
    was_leader = [a._was_leader for a in agents]
    print(f"Initial scores: {scores}")
    print(f"Agents: {[a.plus_n for a in agents]}")
    while any(active):
        roll_count += 1
        die1, die2 = random.randint(1, 6), random.randint(1, 6)
        dice_sum = die1 + die2
        bank += dice_sum
        print(f"\nRoll {roll_count}: {die1} + {die2} = {dice_sum}, bank={bank}")
        for i, agent in enumerate(agents):
            if not active[i]:
                continue
            obs = DummyObservation(
                {
                    "roll_count": roll_count,
                    "can_bank": True,
                    "player_id": i,
                    "player_score": scores[i],
                    "current_bank": bank,
                    "all_player_scores": {j: scores[j] for j in range(4)},
                }
            )
            action = agent.act(obs)
            wait_counters[i] = agent._wait_counter
            was_leader[i] = agent._was_leader
            print(
                f"  Agent {i} (plus_n={agent.plus_n}): score={scores[i]}, wait={wait_counters[i]}, was_leader={was_leader[i]}, action={action}"
            )
            if action == "bank":
                scores[i] += bank
                active[i] = False
                print(f"    Agent {i} BANKS! New score: {scores[i]}")
        if all(not a for a in active):
            print("All agents have banked. Round over.")
            break
        # Optionally, simulate a 7 or other round-ending event here


if __name__ == "__main__":
    simulate_leaderplus_round()
