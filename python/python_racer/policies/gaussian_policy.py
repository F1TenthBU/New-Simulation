import numpy as np
from .base_policy import StructuredPolicy
from python_racer.types.observations import RacecarObservation
from python_racer.types.actions import RacecarAction

class GaussianPolicy(StructuredPolicy):
    """Policy that evaluates trajectories using gaussian scoring."""
    
    def __init__(
        self,
        num_angle_samples: int = 7,    # Number of steering angles to try
        num_speed_samples: int = 5,    # Number of speeds to try
        prediction_steps: int = 20,    # Points per trajectory
        prediction_time: float = 1.0,  # How far to predict
        sigma: float = 1.0,           # Gaussian standard deviation
    ):
        self.num_angle_samples = num_angle_samples
        self.num_speed_samples = num_speed_samples
        self.prediction_steps = prediction_steps
        self.prediction_time = prediction_time
        self.sigma = sigma
        
        # Pre-compute steering and speed options
        self.steering_options = np.linspace(-1.0, 1.0, num_angle_samples)
        self.speed_options = np.linspace(0.2, 1.0, num_speed_samples)
        
        # Pre-compute time steps
        self.dt = self.prediction_time / (self.prediction_steps - 1)
        
        # Pre-compute action combinations
        steering_grid, speed_grid = np.meshgrid(self.steering_options, self.speed_options)
        self.actions = np.stack([steering_grid.flatten(), speed_grid.flatten()], axis=1)
    
    def predict_trajectories(
        self,
        linear_accel: np.ndarray,
        angular_vel: np.ndarray
    ) -> np.ndarray:
        """Predict trajectories for all action combinations at once."""
        SCALE = 10.0
        forward_speed = linear_accel[2] * SCALE
        turn_rate = -angular_vel[1]
        
        num_actions = len(self.actions)
        
        # Initialize trajectories array: [num_actions, num_steps, 2]
        trajectories = np.zeros((num_actions, self.prediction_steps, 2))
        
        # Initialize angles array with zeros
        angles = np.zeros((num_actions, self.prediction_steps))
        
        # Compute effective turn rates for each action
        effective_turn = turn_rate + self.actions[:, 0] * 2.0  # [num_actions]
        
        # Compute cumulative angles for each time step
        for i in range(1, self.prediction_steps):
            angles[:, i] = angles[:, i-1] + effective_turn * self.dt
        
        # Compute velocities for each action
        speeds = self.actions[:, 1] * forward_speed  # [num_actions]
        
        # Compute position changes for each step
        for i in range(1, self.prediction_steps):
            # Update positions based on current angle and speed
            trajectories[:, i, 0] = trajectories[:, i-1, 0] + speeds * np.sin(angles[:, i]) * self.dt
            trajectories[:, i, 1] = trajectories[:, i-1, 1] + speeds * np.cos(angles[:, i]) * self.dt
        
        return trajectories
    
    def score_trajectories(
        self,
        trajectories: np.ndarray,
        lidar_ranges: np.ndarray
    ) -> np.ndarray:
        """Score all trajectories at once."""
        # Initialize LIDAR angles if needed
        if self.lidar_angles is None or len(self.lidar_angles) != len(lidar_ranges):
            self.lidar_angles = np.linspace(-135, 135, len(lidar_ranges)) * np.pi / 180
        
        # Convert LIDAR to cartesian
        lidar_x = lidar_ranges * np.sin(self.lidar_angles)
        lidar_y = lidar_ranges * np.cos(self.lidar_angles)
        obstacles = np.stack([lidar_x, lidar_y], axis=1)  # [num_obstacles, 2]
        
        # Reshape for broadcasting
        trajectories_expanded = trajectories[:, :, np.newaxis, :]  # [num_actions, num_steps, 1, 2]
        obstacles_expanded = obstacles[np.newaxis, np.newaxis, :, :]  # [1, 1, num_obstacles, 2]
        
        # Compute distances for all combinations at once
        distances = np.sum((trajectories_expanded - obstacles_expanded) ** 2, axis=3)  # [num_actions, num_steps, num_obstacles]
        
        # Compute gaussian values
        gaussian_values = np.exp(-distances / (2 * self.sigma ** 2))
        
        # Sum over steps and obstacles - lower is better (less interaction with obstacles)
        obstacle_scores = np.sum(gaussian_values, axis=(1,2))  # [num_actions]
        
        # Compute total distance traveled for each trajectory
        trajectory_distances = np.sqrt(
            np.sum(
                np.diff(trajectories, axis=1) ** 2,  # Squared differences between consecutive points
                axis=2                               # Sum x and y components
            )
        )  # [num_actions, num_steps-1]
        distance_scores = np.sum(trajectory_distances, axis=1)  # Total distance for each trajectory
        
        # Normalize distance scores to [0, 1] range
        distance_scores = (distance_scores - np.min(distance_scores)) / (np.max(distance_scores) - np.min(distance_scores) + 1e-6)
        
        # Add small steering penalty to prefer smoother paths
        steering_penalty = np.abs(self.actions[:, 0]) * 0.05
        
        # Combine scores (negative because we want to minimize gaussian sum)
        return -(obstacle_scores + steering_penalty - distance_scores)
    
    def act(self, obs: RacecarObservation) -> RacecarAction:
        """Choose action by evaluating multiple trajectories."""
        # Predict all trajectories
        trajectories = self.predict_trajectories(
            obs.linear_accel,
            obs.angular_vel
        )
        
        # Score all trajectories
        scores = self.score_trajectories(trajectories, obs.lidar_ranges)
        
        # Get best action (maximum score)
        best_idx = np.argmax(scores)
        steering, acceleration = self.actions[best_idx]
        
        return RacecarAction(steering=float(steering), acceleration=float(acceleration))
    
    def reset(self) -> None:
        """Reset policy state."""
        self.lidar_angles = None