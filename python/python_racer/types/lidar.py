import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

# LIDAR constants from Unity (Lidar.cs)
UNITY_NUM_SAMPLES = 1440      # Total samples in Unity
UNITY_START_ANGLE = 135       # degrees, clockwise from forward
UNITY_END_ANGLE = 270.25      # degrees
UNITY_MIN_RANGE = 2.0         # cm
UNITY_MAX_RANGE = 1000.0      # cm (10m)
PYTHON_NUM_SAMPLES = 1080     # Actual samples we receive (based on Hokuyo LIDAR's 270.25° field of view)
UNITY_FOV = UNITY_END_ANGLE - UNITY_START_ANGLE  # Field of view in degrees

@dataclass
class Lidar:
    """Class representing LIDAR data and providing helper functions."""
    
    ranges: np.ndarray  # Raw LIDAR ranges in cm
    
    def __post_init__(self):
        """Validate LIDAR data."""
        if len(self.ranges) != PYTHON_NUM_SAMPLES:
            raise ValueError(
                f"Expected {PYTHON_NUM_SAMPLES} LIDAR samples, got {len(self.ranges)}"
            )
    
    @property
    def angles(self) -> np.ndarray:
        """Get angles in radians for each LIDAR sample."""
        return np.radians(
            np.linspace(UNITY_START_ANGLE, UNITY_END_ANGLE, PYTHON_NUM_SAMPLES)
        )
    
    def to_cartesian(self, 
                    min_range: float = UNITY_MIN_RANGE,
                    max_range: float = UNITY_MAX_RANGE) -> np.ndarray:
        """
        Convert LIDAR polar coordinates (ranges) to Cartesian coordinates.
        
        Returns:
            Nx2 array of (x, y) points in cm, where:
            - (0,0) is the LIDAR center
            - +x is to the right
            - +y is forward
            Only returns valid readings (between min_range and max_range).
        """
        # Filter valid readings
        valid_mask = (self.ranges >= min_range) & (self.ranges <= max_range)
        valid_ranges = self.ranges[valid_mask]
        valid_angles = self.angles[valid_mask]
        
        if len(valid_ranges) == 0:
            return np.zeros((0, 2))
        
        # Convert to Cartesian coordinates
        x = valid_ranges * np.sin(-valid_angles)  # right is positive
        y = valid_ranges * np.cos(-valid_angles)  # forward is positive
        
        return np.column_stack([x, y])
    
    def get_closest_point(self) -> Tuple[np.ndarray, float]:
        """Get closest valid LIDAR point and its distance."""
        points = self.to_cartesian()
        if len(points) == 0:
            return np.array([0, 0]), UNITY_MAX_RANGE
            
        distances = np.linalg.norm(points, axis=1)
        closest_idx = np.argmin(distances)
        return points[closest_idx], distances[closest_idx]
    
    def get_forward_distance(self, angle_threshold: float = 5.0) -> float:
        """
        Get distance to obstacle directly forward.
        
        Args:
            angle_threshold: Maximum angle (in degrees) from forward to consider
        """
        points = self.to_cartesian()
        if len(points) == 0:
            return UNITY_MAX_RANGE
            
        # Consider points within threshold angle from forward direction
        vectors = points / np.linalg.norm(points, axis=1, keepdims=True)
        forward_angles = np.arccos(vectors[:, 1])  # dot product with [0, 1]
        forward_mask = forward_angles < np.radians(angle_threshold)
        forward_points = points[forward_mask]
        
        if len(forward_points) == 0:
            return UNITY_MAX_RANGE
            
        return np.min(np.linalg.norm(forward_points, axis=1))
    
    def get_sector_distances(self, num_sectors: int = 5) -> np.ndarray:
        """
        Get minimum distances in each sector.
        
        Args:
            num_sectors: Number of sectors to divide the field of view into
            
        Returns:
            Array of minimum distances for each sector, from left to right
        """
        points = self.to_cartesian()
        if len(points) == 0:
            return np.full(num_sectors, UNITY_MAX_RANGE)
            
        # Calculate angles of points (in range -UNITY_FOV/2 to UNITY_FOV/2)
        angles = np.arctan2(points[:, 0], points[:, 1])  # in radians
        
        # Define sector boundaries
        sector_bounds = np.radians(
            np.linspace(-UNITY_FOV/2, UNITY_FOV/2, num_sectors + 1)
        )
        
        # Calculate minimum distance in each sector
        sector_distances = []
        for i in range(num_sectors):
            sector_mask = (angles >= sector_bounds[i]) & (angles < sector_bounds[i + 1])
            sector_points = points[sector_mask]
            if len(sector_points) == 0:
                sector_distances.append(UNITY_MAX_RANGE)
            else:
                sector_distances.append(np.min(np.linalg.norm(sector_points, axis=1)))
                
        return np.array(sector_distances)
    
    def get_gaussian_map(self, 
                        x_res: int = 100, 
                        y_res: int = 100, 
                        sigma: float = 4.5) -> np.ndarray:
        """
        Create a Gaussian occupancy map from LIDAR data.
        
        Args:
            x_res: Resolution in x direction
            y_res: Resolution in y direction
            sigma: Standard deviation for Gaussian blur
            
        Returns:
            2D numpy array representing occupancy probability
        """
        points = self.to_cartesian()
        if len(points) == 0:
            return np.zeros((y_res, x_res))
            
        # Scale points to grid coordinates
        scale = min(x_res, y_res) / (2 * UNITY_MAX_RANGE)
        grid_points = points * scale + np.array([x_res/2, y_res/2])
        grid_points = grid_points.astype(int)
        
        # Filter points within bounds
        valid_mask = (grid_points[:, 0] >= 0) & (grid_points[:, 0] < x_res) & \
                    (grid_points[:, 1] >= 0) & (grid_points[:, 1] < y_res)
        grid_points = grid_points[valid_mask]
        
        # Create Gaussian template
        radius = int(3 * sigma)
        x, y = np.meshgrid(np.arange(-radius, radius + 1), np.arange(-radius, radius + 1))
        gaussian_template = np.exp(-(x**2 + y**2) / (2 * sigma**2))
        
        # Create occupancy map
        occupancy_map = np.zeros((y_res, x_res))
        for point in grid_points:
            x_start = max(0, point[0] - radius)
            x_end = min(x_res, point[0] + radius + 1)
            y_start = max(0, point[1] - radius)
            y_end = min(y_res, point[1] + radius + 1)
            
            template_x_start = max(0, radius - point[0])
            template_y_start = max(0, radius - point[1])
            template_x_end = template_x_start + (x_end - x_start)
            template_y_end = template_y_start + (y_end - y_start)
            
            occupancy_map[y_start:y_end, x_start:x_end] += \
                gaussian_template[template_y_start:template_y_end, 
                                template_x_start:template_x_end]
                
        return occupancy_map
    
    def get_closest_obstacle(self) -> Tuple[float, int]:
        """
        Get distance and index of closest obstacle.
        
        Returns:
            Tuple of (distance in cm, index in LIDAR array)
        """
        valid_mask = (self.ranges >= UNITY_MIN_RANGE) & (self.ranges <= UNITY_MAX_RANGE)
        if not np.any(valid_mask):
            return UNITY_MAX_RANGE, len(self.ranges) // 2
            
        valid_ranges = self.ranges[valid_mask]
        valid_indices = np.where(valid_mask)[0]
        min_idx = np.argmin(valid_ranges)
        return valid_ranges[min_idx], valid_indices[min_idx]
        