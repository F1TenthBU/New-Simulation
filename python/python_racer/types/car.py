from dataclasses import dataclass
import numpy as np
from typing import Optional, Tuple, List

# Constants for car physics
MAX_SPEED = 200.0  # cm/s
MAX_TURN_RATE = np.pi/4  # rad/s
MAX_STEERING_ANGLE = 35.0  # degrees

@dataclass
class CarState:
    """Represents the current state of the car."""
    position: np.ndarray  # [x, y] in cm
    orientation: float    # angle in radians (0 = forward)
    velocity: float      # forward velocity in cm/s
    angular_velocity: float  # angular velocity in rad/s
    steering_angle: float   # current steering angle in degrees

    @classmethod
    def from_raw(cls,
                linear_accel: np.ndarray,
                angular_vel: np.ndarray,
                steering_angle: float = 0.0,
                dt: float = 0.1) -> 'CarState':
        """
        Create car state from raw sensor data.
        
        Args:
            linear_accel: Linear acceleration in m/s^2 [x, y, z]
            angular_vel: Angular velocity in rad/s [x, y, z]
            steering_angle: Current steering angle in degrees
            dt: Time step for velocity approximation
        """
        # Start at origin facing forward
        position = np.zeros(2)
        orientation = 0.0
        
        # Approximate velocity from acceleration
        # Unity uses Z-axis as forward
        velocity = linear_accel[2] * dt * 100  # Convert to cm/s
        
        # Unity uses Y-axis for turning
        angular_velocity = -angular_vel[1]  # Flip sign to match our coordinate system
        
        return cls(
            position=position,
            orientation=orientation,
            velocity=velocity,
            angular_velocity=angular_velocity,
            steering_angle=steering_angle
        )

class Car:
    """Class representing a car and its dynamics."""
    
    def __init__(self,
                max_speed: float = MAX_SPEED,
                max_turn_rate: float = MAX_TURN_RATE,
                max_steering_angle: float = MAX_STEERING_ANGLE):
        self.max_speed = max_speed
        self.max_turn_rate = max_turn_rate
        self.max_steering_angle = max_steering_angle
    
    def predict_path(self,
                    state: CarState,
                    num_points: int = 20,
                    prediction_time: float = 1.0,
                    min_speed: float = 0.1) -> np.ndarray:
        """
        Predict car's path based on current state.
        
        Args:
            state: Current car state
            num_points: Number of points to predict
            prediction_time: How far into the future to predict (seconds)
            min_speed: Minimum speed to consider for prediction
            
        Returns:
            Array of shape (num_points, 2) containing predicted (x, y) positions
        """
        # If nearly stopped, just show a short line forward
        if abs(state.velocity) < min_speed:
            y = np.linspace(0, self.max_speed * 0.2, num_points)
            x = np.zeros_like(y)
            return np.column_stack([x, y]).astype(np.float32)
        
        # Calculate time steps
        times = np.linspace(0, prediction_time, num_points)
        dt = times[1] - times[0]
        
        # Initialize arrays for path
        positions = np.zeros((num_points, 2))
        orientation = state.orientation
        
        # Start from current state
        positions[0] = state.position
        velocity = state.velocity
        angular_velocity = state.angular_velocity
        
        # For each time step, update state and calculate new position
        for i in range(1, num_points):
            # Update orientation based on angular velocity
            orientation += angular_velocity * dt
            
            # Calculate movement in car's local frame
            dx = velocity * np.sin(orientation) * dt
            dy = velocity * np.cos(orientation) * dt
            
            # Update position
            positions[i] = positions[i-1] + [dx, dy]
        
        return positions.astype(np.float32)
    
    def predict_multiple_paths(self,
                             state: CarState,
                             steering_angles: np.ndarray,
                             speeds: np.ndarray,
                             num_points: int = 20,
                             prediction_time: float = 1.0) -> np.ndarray:
        """
        Predict multiple possible paths for different control inputs.
        
        Args:
            state: Current car state
            steering_angles: Array of steering angles to try (degrees)
            speeds: Array of speeds to try (cm/s)
            num_points: Number of points per path
            prediction_time: How far to predict each path
            
        Returns:
            Array of shape (num_paths, num_points, 2) containing predicted paths
        """
        # Create all combinations of steering angles and speeds
        angle_grid, speed_grid = np.meshgrid(steering_angles, speeds)
        num_paths = len(angle_grid.flatten())
        
        # Initialize array for all paths
        paths = np.zeros((num_paths, num_points, 2))
        
        # For each combination
        for i, (angle, speed) in enumerate(zip(angle_grid.flatten(), speed_grid.flatten())):
            # Create new state with this control input
            new_state = CarState(
                position=state.position,
                orientation=state.orientation,
                velocity=speed,
                angular_velocity=np.deg2rad(angle) * self.max_turn_rate / self.max_steering_angle,
                steering_angle=angle
            )
            
            # Predict path for this state
            paths[i] = self.predict_path(new_state, num_points, prediction_time)
        
        return paths 