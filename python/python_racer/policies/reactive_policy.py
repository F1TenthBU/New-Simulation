import numpy as np
from .base_policy import StructuredPolicy
from python_racer.types.observations import RacecarObservation
from python_racer.types.actions import RacecarAction

class ReactivePolicy(StructuredPolicy):
    """Simple reactive policy that steers away from obstacles."""
    
    def __init__(self, min_speed: float = 0.3, max_speed: float = 1.0):
        self.min_speed = min_speed
        self.max_speed = max_speed
    
    def act(self, obs: RacecarObservation) -> RacecarAction:
        # Get closest obstacle
        min_dist, min_idx = obs.lidar.get_closest_obstacle()
        
        # Calculate steering based on obstacle position
        # Convert index to angle: assuming LIDAR covers 270 degrees (-135 to +135)
        angle_range = 270
        mid_idx = len(obs.lidar.ranges) // 2
        angle = (min_idx - mid_idx) / mid_idx * (angle_range/2)
        
        # Steer away from obstacle
        steering = -np.clip(angle / 135.0, -1.0, 1.0)
        
        # Adjust speed based on forward clearance
        forward_dist = obs.lidar.get_forward_distance()
        acceleration = np.clip(
            forward_dist / 10.0,  # Scale distance to speed
            self.min_speed,       # Maintain minimum speed
            self.max_speed        # Cap at maximum speed
        )
        
        return RacecarAction(steering=steering, acceleration=acceleration)
    
    def reset(self) -> None:
        pass

class PurePursuitPolicy(StructuredPolicy):
    """Policy that follows a target point on the track."""
    
    def __init__(self, lookahead: float = 5.0):
        self.lookahead = lookahead
    
    def act(self, obs: RacecarObservation) -> RacecarAction:
        # Get sector distances to find best path
        sectors = obs.lidar.get_sector_distances(5)
        
        # Find sector with most clearance
        best_sector = np.argmax(sectors)
        
        # Convert sector to steering angle
        steering = (best_sector - 2) / 2.0  # -1 to 1 based on sector
        
        # Use constant acceleration for now
        acceleration = 0.5
        
        return RacecarAction(steering=steering, acceleration=acceleration)
    
    def reset(self) -> None:
        pass