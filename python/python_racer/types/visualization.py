from dataclasses import dataclass
from typing import List
import numpy as np
from python_racer.renderers.arcs.renderer import Arc
from .geometry import Gaussians

@dataclass
class Visualization:
    arcs: List[Arc]
    gaussians: Gaussians
    
    @staticmethod
    def empty() -> 'Visualization':
        """Create an empty visualization."""
        return Visualization(
            arcs=[],
            gaussians=Gaussians(
                pos=np.zeros((0, 2), dtype=np.float32),
                std=np.zeros(0, dtype=np.float32),
                intensity=np.zeros(0, dtype=np.float32)
            )
        )
    
    @staticmethod
    def compose(*visualizations: 'Visualization') -> 'Visualization':
        """Compose multiple visualizations into one."""
        return Visualization(
            arcs=[arc for viz in visualizations for arc in viz.arcs],
            gaussians=Gaussians(
                pos=np.concatenate([viz.gaussians.pos for viz in visualizations]),
                std=np.concatenate([viz.gaussians.std for viz in visualizations]),
                intensity=np.concatenate([viz.gaussians.intensity for viz in visualizations])
            )
        )