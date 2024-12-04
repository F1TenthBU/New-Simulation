from dataclasses import dataclass
import numpy as np

@dataclass
class RacecarAction:
    """Human-readable racecar control action."""
    steering: float  # Range: [-1, 1]
    acceleration: float  # Range: [-1, 1]
    
    def numpy(self) -> np.ndarray:
        """Convert to numpy array for gym interface."""
        return np.array([self.steering, self.acceleration], dtype=np.float32)
    
    @classmethod
    def from_numpy(cls, action: np.ndarray) -> 'RacecarAction':
        """Create from numpy array."""
        return cls(steering=float(action[0]), acceleration=float(action[1]))