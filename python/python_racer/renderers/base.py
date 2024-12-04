from typing import Protocol, runtime_checkable
from python_racer.events.window_events import RenderEvent
from python_racer.types.geometry import Rectangle

@runtime_checkable
class Renderer(Protocol):
    """Protocol defining the interface for renderers."""
    
    def render(self, event: RenderEvent) -> None:
        """Render using the provided render event."""
        ...
        
    def update_view_uniforms(self, rect: Rectangle) -> None:
        """Update view uniform buffer with new rectangle."""
        ... 