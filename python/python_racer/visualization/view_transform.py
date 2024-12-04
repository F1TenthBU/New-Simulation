from dataclasses import dataclass, replace
import numpy as np
from ..events.emitter import EventEmitter
from ..types.geometry import Rectangle
from ..events.window_events import WindowEvents

def create_world_rect_stream(initial_size: tuple[int, int], events: WindowEvents, initial_world_height: float = 50.0) -> EventEmitter[Rectangle]:
    """
    Create world rect stream that responds to window events.
    initial_world_height determines the initial view scale - objects will be sized relative to this.
    """
    width, height = initial_size
    
    # Calculate initial world size to match screen aspect ratio
    aspect_ratio = width / height
    initial_world_size = np.array([
        initial_world_height * aspect_ratio,
        initial_world_height
    ])
    
    # Create world rect stream
    world_rect = EventEmitter[Rectangle]()
    world_rect.emit(Rectangle(
        center=np.zeros(2),
        size=initial_world_size
    ))
    
    # Apply patches from window events
    return world_rect.apply_patches(
        # Resize patches - scale by window size ratio
        events.resize.map(
            lambda e: lambda rect: Rectangle(
                center=rect.center,
                size=rect.size * (e.size / e.previous_size)  # Scale by ratio of sizes
            )
        ),
        
        # Zoom patches
        events.scroll.map(
            lambda e: lambda rect: Rectangle(
                center=rect.center,
                size=rect.size * (0.9 if e.offset[1] > 0 else 1.1)
            )
        ),
        
        # Pan patches - delta is already normalized
        events.mouse_drag.map(
            lambda e: lambda rect: replace(rect,
                center=rect.center - e.delta * rect.size
            )
        )
    )
