"""
Environment for training and evaluating racecar policies.
"""

import gymnasium as gym
import numpy as np
from typing import Any, Dict, Tuple
from pathlib import Path
import os
from mlagents_envs.environment import UnityEnvironment
from mlagents_envs.side_channel.engine_configuration_channel import EngineConfigurationChannel
from mlagents_envs.base_env import ActionTuple
from python_racer.types.observations import RacecarObservation
from python_racer.types.actions import RacecarAction

def get_sim_path() -> str:
    """Get the path to the Unity simulator executable."""
    root = str(Path(__file__).parents[3])
    return os.path.join(root, "Builds", "sim")

class RacecarEnv(gym.Env):
    """
    Gym environment for the racecar.
    
    Wraps the Unity ML-Agents environment to provide a standard gym interface.
    """
    
    def __init__(self, env_path: str = None, time_scale: float = 20.0):
        """
        Create a new racecar environment.
        
        Args:
            env_path: Path to Unity environment executable. If None, uses default path.
            time_scale: Unity time scale (higher is faster)
        """
        # Configure Unity environment
        self.engine_configuration_channel = EngineConfigurationChannel()
        self.engine_configuration_channel.set_configuration_parameters(
            time_scale=time_scale,
            target_frame_rate=-1,  # No frame rate cap
            capture_frame_rate=60,
        )
        
        # Create Unity environment
        if env_path is None:
            env_path = get_sim_path()
            
        self.unity_env = UnityEnvironment(
            file_name=env_path,
            side_channels=[self.engine_configuration_channel],
            no_graphics=True,
        )
        self.unity_env.reset()
        
        # Get behavior name and spec
        self.behavior_name = list(self.unity_env.behavior_specs)[0]
        behavior_spec = self.unity_env.behavior_specs[self.behavior_name]
        
        # Set up observation and action spaces
        self.observation_space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=behavior_spec.observation_specs[0].shape,
            dtype=np.float32,
        )
        
        self.action_space = gym.spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(2,),  # [steering, acceleration]
            dtype=np.float32,
        )
    
    def reset(self, seed: int = None, options: Dict = None) -> Tuple[np.ndarray, Dict]:
        """
        Reset the environment.
        
        Args:
            seed: Random seed (unused)
            options: Additional options (unused)
            
        Returns:
            Initial observation and info dict
        """
        # Reset Unity environment
        self.unity_env.reset()
        
        # Get initial observation
        decision_steps, _ = self.unity_env.get_steps(self.behavior_name)
        raw_obs = decision_steps.obs[0][0]
        structured_obs = RacecarObservation.from_unity_obs(raw_obs)
        
        # Return observation and info
        info = {
            'min_distance': np.min(structured_obs.lidar.ranges),
            'collision': structured_obs.collision,
        }
        return raw_obs, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Take a step in the environment.
        
        Args:
            action: Array of [steering, acceleration] in range [-1, 1]
            
        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        # Convert to structured action
        structured_action = RacecarAction(
            steering=float(action[0]),
            acceleration=float(action[1])
        )
        
        # Send action to Unity
        action_tuple = ActionTuple(
            continuous=np.array([[structured_action.steering, structured_action.acceleration]], dtype=np.float32)
        )
        self.unity_env.set_actions(self.behavior_name, action_tuple)
        self.unity_env.step()
        
        # Get result
        decision_steps, terminal_steps = self.unity_env.get_steps(self.behavior_name)
        
        # Check if episode ended
        done = len(terminal_steps.agent_id) > 0
        if done:
            raw_obs = terminal_steps.obs[0][0]
            reward = terminal_steps.reward[0]
        else:
            raw_obs = decision_steps.obs[0][0]
            reward = decision_steps.reward[0]
        
        # Convert to structured observation
        structured_obs = RacecarObservation.from_unity_obs(raw_obs)
        
        # Return step result
        info = {
            'min_distance': np.min(structured_obs.lidar.ranges),
            'collision': structured_obs.collision,
        }
        return raw_obs, reward, done, False, info
    
    def close(self):
        """Close the environment."""
        self.unity_env.close()
    
    def render(self):
        """Rendering is handled by Unity."""
        pass