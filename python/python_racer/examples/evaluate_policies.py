from python_racer.policies.base_policy import StructuredPolicy, FlattenedPolicy
from python_racer.types.observations import RacecarObservation
from python_racer.types.actions import RacecarAction
from python_racer.visualization.visualizer import Visualizer
from python_racer.visualization.window_process import VisualizationWindow
from python_racer.envs.racecar_env import RacecarEnv
import numpy as np
from dataclasses import dataclass

@dataclass
class EvalResult:
    """Results from policy evaluation."""
    total_reward: float
    episode_length: int
    average_speed: float
    collision_count: int
    distance_traveled: float

def evaluate_policy(
    policy: StructuredPolicy,
    visualizer: Visualizer = Visualizer.compose(),
    num_episodes: int = 5,
    time_scale: float = 1.0
) -> list[EvalResult]:
    """
    Evaluate a policy over multiple episodes with optional visualization.
    
    Args:
        policy: The policy to evaluate
        visualizer: Optional visualizer for rendering policy behavior
        num_episodes: Number of episodes to evaluate
        time_scale: Speed multiplier for simulation (>1 for faster)
    
    Returns:
        List of evaluation results per episode
    """
    # Create environment and wrap policy
    env = RacecarEnv(time_scale=time_scale)
    flattened_policy = FlattenedPolicy(policy)
    
    # Create visualization window if visualizer provided
    window = VisualizationWindow() if visualizer else None
    
    results = []
    try:
        for episode in range(num_episodes):
            observation, info = env.reset()
            policy.reset()
            
            total_reward = 0
            step_count = 0
            collision_count = 0
            total_speed = 0
            
            while True:
                # Convert flat observation to structured
                structured_obs = RacecarObservation.from_unity_obs(observation)
                
                # Get action from policy
                action = flattened_policy.act(observation)
                
                # Update visualization if provided
                if visualizer and window:
                    viz = visualizer.visualize(structured_obs, RacecarAction.from_numpy(action))
                    window.update(viz)
                
                # Take step in environment
                observation, reward, terminated, truncated, info = env.step(action)
                
                # Update statistics
                total_reward += reward
                step_count += 1
                total_speed += info.get('velocity', 0)
                if info.get('collision', False):
                    collision_count += 1
                
                if terminated or truncated:
                    break
            
            # Record episode results
            result = EvalResult(
                total_reward      = total_reward,
                episode_length    = step_count,
                average_speed     = total_speed / step_count,
                collision_count   = collision_count,
                distance_traveled = info.get('total_distance', 0)
            )
            results.append(result)
            
            # Print episode results
            print(f"\nEpisode {episode + 1} results:")
            print(f"Total reward: {total_reward:.2f}")
            print(f"Episode length: {step_count}")
            print(f"Average speed: {total_speed/step_count:.2f}")
            print(f"Collisions: {collision_count}")
            print(f"Distance: {info.get('total_distance', 0):.2f}")
    
    finally:
        if window:
            window.close()
        env.close()
    
    return results

def print_summary(results: list[EvalResult], policy_name: str) -> None:
    """Print summary statistics for all episodes."""
    avg_reward     = np.mean([r.total_reward      for r in results])
    avg_length     = np.mean([r.episode_length    for r in results])
    avg_speed      = np.mean([r.average_speed     for r in results])
    avg_collisions = np.mean([r.collision_count   for r in results])
    avg_distance   = np.mean([r.distance_traveled for r in results])
    
    print(f"\nSummary for {policy_name}:")
    print(f"Average reward: {avg_reward:.2f}")
    print(f"Average episode length: {avg_length:.2f}")
    print(f"Average speed: {avg_speed:.2f}")
    print(f"Average collisions: {avg_collisions:.2f}")
    print(f"Average distance: {avg_distance:.2f}")

def main():
    """Example usage of policy evaluation with visualization."""
    from python_racer.policies.reactive_policy import ReactivePolicy
    from python_racer.visualization.visualizer import arc_visualizer, lidar_visualizer, Visualizer
    
    # Create policy
    policy = ReactivePolicy()
    
    # Create visualizer (optional)
    visualizer = Visualizer.compose(
        arc_visualizer(),
        lidar_visualizer()
    )
    
    # Evaluate policy with visualization
    results = evaluate_policy(
        policy       = policy,
        visualizer   = visualizer,
        num_episodes = 3,
        time_scale   = 1.0
    )
    
    # Print summary statistics
    print_summary(results, policy.__class__.__name__)

if __name__ == "__main__":
    main() 