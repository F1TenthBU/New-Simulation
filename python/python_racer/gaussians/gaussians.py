from dataclasses import dataclass
from typing import NamedTuple
import numpy as np

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