from dataclasses import dataclass
from typing import Callable, Protocol
import numpy as np
from python_racer.types.observations import RacecarObservation

class RewardFunction(Protocol):
    """Interface for reward functions that work with structured observations."""
    def __call__(self, obs: RacecarObservation, action: np.ndarray) -> float:
        ...

def default_reward(obs: RacecarObservation, action: np.ndarray) -> float:
    """Default reward function using structured observation."""
    steering, acceleration = action
    velocity = np.linalg.norm(obs.linear_accel)
    forward_progress = obs.linear_accel[2]  # Z-axis is forward
    
    reward = (
        forward_progress * 1.0 +     # Reward forward motion
        -abs(steering) * 0.1         # Small penalty for steering
    )
    
    # Penalty for being too close to obstacles
    min_dist = np.min(obs.lidar_ranges)
    if min_dist < 1.0:
        reward -= (1.0 - min_dist)
    
    return reward

class FlattenedReward:
    """Wrapper that converts flat observations to structured for reward calculation."""
    
    def __init__(self, structured_reward: RewardFunction):
        self.structured_reward = structured_reward
    
    def __call__(self, flat_obs: np.ndarray, action: np.ndarray) -> float:
        structured_obs = RacecarObservation.from_unity_obs(flat_obs)
        return self.structured_reward(structured_obs, action) 