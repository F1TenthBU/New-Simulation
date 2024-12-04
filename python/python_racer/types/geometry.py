"""Common geometric types and utilities."""

from dataclasses import dataclass
from typing import NamedTuple
import numpy as np

@dataclass(frozen=True)
class Rectangle:
    """Rectangle with center point and size."""
    center: np.ndarray  # [x, y]
    size: np.ndarray    # [width, height]
    
    def transform_point_to(self, point: np.ndarray, other: 'Rectangle') -> np.ndarray:
        """Transform a point from this rectangle's space to another's."""
        # First transform to normalized space [-1, 1]
        normalized = (point - self.center) / (self.size * 0.5)
        # Then transform to target space
        return normalized * (other.size * 0.5) + other.center

# @dataclass(frozen=True)
class Gaussians(NamedTuple):
    pos: np.ndarray       # shape: (n, 2)
    std: np.ndarray      # shape: (n,)
    intensity: np.ndarray # shape: (n,)

def create_random_gaussians(n_points: int = 1_000_000, spread: float = 5000.0) -> Gaussians:
    rng = np.random.default_rng(0)
    return Gaussians(
        pos=rng.normal(0, spread, size=(n_points, 2)),
        std=np.exp(rng.normal(0, 1, size=n_points)) * 1.0,
        intensity=rng.uniform(0.5, 1.0, size=n_points)
    ) 

@dataclass(frozen=True)
class Arc:
    """Arc data for visualization."""
    points: np.ndarray  # Shape: [N, 2]
    color: np.ndarray   # Shape: [4] RGBA
    width: float = 0.2  # Line width in world units
