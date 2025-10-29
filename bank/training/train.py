"""
Training Script

Main training loop for DQN agents.
"""

import click
from typing import Optional


@click.command()
@click.option("--episodes", "-e", default=1000, help="Number of training episodes")
@click.option("--players", "-p", default=2, help="Number of players")
@click.option("--save-path", "-s", default="models/dqn_agent.pth", help="Path to save trained model")
@click.option("--load-path", "-l", default=None, help="Path to load existing model")
def main(episodes: int, players: int, save_path: str, load_path: Optional[str]):
    """
    Train a DQN agent to play BANK!
    
    This script trains a Deep Q-Network agent using self-play and/or
    against other agents.
    """
    try:
        import torch
        import numpy as np
        from bank.training.environment import BankEnv
        from bank.training.dqn_agent import DQNAgent
    except ImportError as e:
        click.echo(f"Error: Missing required dependencies for training.")
        click.echo(f"Install with: pip install bank-game[ml]")
        click.echo(f"Details: {e}")
        return
    
    click.echo("=" * 50)
    click.echo("DQN Training for BANK!")
    click.echo("=" * 50)
    click.echo(f"Episodes: {episodes}")
    click.echo(f"Players: {players}")
    click.echo()
    
    # Create environment
    env = BankEnv(num_players=players)
    
    # Create agent
    agent = DQNAgent(player_id=0, name="DQN-Trainee")
    
    if load_path:
        click.echo(f"Loading model from {load_path}")
        agent.load_model(load_path)
    
    # Training loop
    click.echo("Starting training...")
    
    for episode in range(episodes):
        state, info = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            # Select action (using environment's action space)
            if np.random.random() < agent.epsilon:
                action = env.action_space.sample()
            else:
                with torch.no_grad():
                    state_tensor = torch.FloatTensor(state).unsqueeze(0)
                    q_values = agent.q_network(state_tensor)
                    action = q_values.argmax().item()
            
            # Take action
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            episode_reward += reward
            state = next_state
        
        # Decay exploration
        agent.update_epsilon()
        
        # Log progress
        if (episode + 1) % 100 == 0:
            click.echo(
                f"Episode {episode + 1}/{episodes} - "
                f"Reward: {episode_reward:.2f} - "
                f"Epsilon: {agent.epsilon:.3f}"
            )
    
    # Save model
    click.echo(f"\nSaving model to {save_path}")
    import os
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    agent.save_model(save_path)
    
    click.echo("Training complete!")


if __name__ == "__main__":
    main()
