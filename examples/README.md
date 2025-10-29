# Examples

This directory contains example scripts demonstrating how to use the BANK! framework.

## Available Examples

### `simple_agent.py`
Demonstrates how to create a custom agent with a simple greedy strategy.

```bash
python examples/simple_agent.py
```

### `tournament.py`
Shows how to run multiple games between agents and collect statistics.

```bash
python examples/tournament.py
```

### `inspect_game.py`
Demonstrates how to inspect and analyze game state during play.

```bash
python examples/inspect_game.py
```

## Creating Your Own Examples

Feel free to create your own example scripts! Some ideas:

1. **Strategy Comparison**: Compare different strategies (greedy vs conservative)
2. **Learning Curves**: Track how an agent improves over time
3. **State Visualization**: Create visualizations of game progression
4. **Custom Rules**: Experiment with modified game rules
5. **Multi-Agent Scenarios**: Test agents in 3+ player games

## Running Examples

Make sure the package is installed first:

```bash
# From the repository root
pip install -e .

# Then run any example
python examples/simple_agent.py
```
