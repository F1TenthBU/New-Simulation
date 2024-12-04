from dataclasses import dataclass
import numpy as np
from .lidar import Lidar, PYTHON_NUM_SAMPLES

@dataclass
class RacecarObservation:
    """Class representing a single observation from the racecar environment."""
    
    lidar: Lidar            # LIDAR data
    linear_accel: np.ndarray  # Linear acceleration in m/s^2
    angular_vel: np.ndarray   # Angular velocity in rad/s
    collision: bool           # Whether the car is currently in collision
    
    @classmethod
    def from_unity_obs(cls, obs_array: np.ndarray) -> 'RacecarObservation':
        """
        Convert Unity ML-Agents observation to structured format.
        
        Unity observation format:
        - obs[0][:3] = linear acceleration (x, y, z)
        - obs[0][3:6] = angular velocity (x, y, z)
        - obs[0][6] = collision state (1.0 for collision, 0.0 for no collision)
        - obs[0][7:] = LIDAR ranges (1081 samples, clockwise from 135° to 270.25°)
                      Values are in cm, 0.0 indicates invalid reading
        """
        linear_accel = obs_array[:3]
        angular_vel = obs_array[3:6]
        collision = bool(obs_array[6] > 0.5)
        lidar_ranges = obs_array[7:]
        
        assert len(lidar_ranges) == PYTHON_NUM_SAMPLES, \
            f"Expected {PYTHON_NUM_SAMPLES} LIDAR samples, got {len(lidar_ranges)}"
        
        return cls(
            lidar=Lidar(lidar_ranges),
            linear_accel=linear_accel,
            angular_vel=angular_vel,
            collision=collision,
        )
    
    def get_velocity(self) -> float:
        """Calculate velocity magnitude from linear acceleration."""
        return float(np.linalg.norm(self.linear_accel))