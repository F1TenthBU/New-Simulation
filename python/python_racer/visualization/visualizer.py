from typing import Callable, List
import numpy as np
from python_racer.types.observations import RacecarObservation
from python_racer.types.actions import RacecarAction
from python_racer.types.visualization import Visualization, Arc
from python_racer.types.geometry import Gaussians
from python_racer.types.car import Car, CarState

class Visualizer:
    """Wrapper around a function that produces visualizations from observations and actions."""
    def __init__(self, visualize_fn: Callable[[RacecarObservation, RacecarAction], Visualization]):
        self.visualize_fn = visualize_fn

    def visualize(self, obs: RacecarObservation, act: RacecarAction) -> Visualization:
        """Produce a visualization from the current observation and action."""
        return self.visualize_fn(obs, act)

    @staticmethod
    def compose(*visualizers: 'Visualizer') -> 'Visualizer':
        """Compose multiple visualizers into one."""
        def composed_viz(obs: RacecarObservation, act: RacecarAction) -> Visualization:
            return Visualization.compose(*(v.visualize(obs, act) for v in visualizers))
        return Visualizer(composed_viz)

def arc_visualizer() -> Visualizer:
    """Create a visualizer that predicts and shows the car's motion arc."""
    car = Car()  # Use default physics parameters
    
    def visualize_arc(obs: RacecarObservation, act: RacecarAction) -> Visualization:
        # Create car state from observation
        state = CarState.from_raw(
            linear_accel=obs.linear_accel,
            angular_vel=obs.angular_vel,
            steering_angle=act.steering * car.max_steering_angle
        )
        
        # Predict path
        arc_points = car.predict_path(state)
        
        # Create visualization with arc
        return Visualization(
            arcs=[Arc(
                points=arc_points,
                color=np.array([0.0, 1.0, 0.0, 1.0], dtype=np.float32)
            )],
            gaussians=Gaussians(
                pos=np.zeros((0, 2), dtype=np.float32),
                std=np.zeros(0, dtype=np.float32),
                intensity=np.zeros(0, dtype=np.float32)
            )
        )
    
    return Visualizer(visualize_arc)

def lidar_visualizer() -> Visualizer:
    """Create a visualizer that shows LIDAR data as gaussians."""
    def visualize_lidar(obs: RacecarObservation, act: RacecarAction) -> Visualization:
        # Get LIDAR points in Cartesian coordinates
        points = obs.lidar.to_cartesian()
        
        # Create gaussians from the points
        gaussians = Gaussians(
            pos=points.astype(np.float32),  # points are already in (x,y) format
            std=np.full(len(points), 1.0, dtype=np.float32),  # Larger points
            intensity=np.full(len(points), 0.2, dtype=np.float32)  # Lower intensity
        )
        
        return Visualization(
            arcs=[],
            gaussians=gaussians
        )
    
    return Visualizer(visualize_lidar)

def trajectory_visualizer() -> Visualizer:
    """Create a visualizer that shows multiple possible trajectories."""
    car = Car()  # Use default physics parameters
    
    def visualize_trajectories(obs: RacecarObservation, act: RacecarAction) -> Visualization:
        # Create car state from observation
        state = CarState.from_raw(
            linear_accel=obs.linear_accel,
            angular_vel=obs.angular_vel,
            steering_angle=act.steering * car.max_steering_angle
        )
        
        # Define trajectory options
        steering_angles = np.linspace(-car.max_steering_angle, car.max_steering_angle, 7)
        speeds = np.array([0.2, 0.5, 1.0]) * car.max_speed
        
        # Predict multiple paths
        paths = car.predict_multiple_paths(state, steering_angles, speeds)
        
        # Create arcs for each path with varying colors
        arcs = []
        for i, path in enumerate(paths):
            # Color based on speed and steering
            speed_idx = i // len(steering_angles)
            steer_idx = i % len(steering_angles)
            
            # Red for slow, green for fast
            red = 1.0 - speeds[speed_idx] / car.max_speed
            # Blue for left turn, green for right
            blue = steering_angles[steer_idx] / car.max_steering_angle
            
            arcs.append(Arc(
                points=path,
                color=np.array([red, 0.5, blue, 0.3], dtype=np.float32)
            ))
        
        return Visualization(
            arcs=arcs,
            gaussians=Gaussians(
                pos=np.zeros((0, 2), dtype=np.float32),
                std=np.zeros(0, dtype=np.float32),
                intensity=np.zeros(0, dtype=np.float32)
            )
        )
    
    return Visualizer(visualize_trajectories)

def create_default_visualizer() -> Visualizer:
    """Create the default visualizer with LIDAR points and predicted paths."""
    return Visualizer.compose(
        lidar_visualizer(),
        arc_visualizer(),
        trajectory_visualizer()
    )