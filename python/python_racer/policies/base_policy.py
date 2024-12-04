from typing import Protocol, runtime_checkable
import numpy as np
from python_racer.types.observations import RacecarObservation
from python_racer.types.actions import RacecarAction

@runtime_checkable
class StructuredPolicy(Protocol):
    """Interface for policies that work with structured observations."""
    def act(self, obs: RacecarObservation) -> RacecarAction:
        """
        Compute action based on observation.
        
        Returns:
            RacecarAction containing steering and acceleration
        """
        ...
    
    def reset(self) -> None:
        ...

class FlattenedPolicy:
    """Wrapper that converts a structured policy into a flat one matching the gym interface."""
    
    def __init__(self, structured_policy: StructuredPolicy):
        self.structured_policy = structured_policy
    
    def act(self, flat_obs: np.ndarray) -> np.ndarray:
        # Convert flat observation to structured
        structured_obs = RacecarObservation.from_unity_obs(flat_obs)
        
        # Get action from structured policy
        action = self.structured_policy.act(structured_obs)
        
        # Convert action to numpy array
        return np.array([action.steering, action.acceleration], dtype=np.float32)
    
    def reset(self) -> None:
        self.structured_policy.reset()