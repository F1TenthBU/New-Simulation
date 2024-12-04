import multiprocessing as mp
from python_racer.types.visualization import Visualization
from python_racer.renderers.arcs.renderer import ArcRenderer
from python_racer.renderers.gaussians.renderer import GaussianRenderer
from python_racer.visualization.window_state import WindowState
from python_racer.events.emitter import EventEmitter

class VisualizationWindow:
    """Window that renders visualizations using WebGPU in a separate process."""
    
    def __init__(self, width: int = 1024, height: int = 768, title: str = "Visualization"):
        self.viz_queue = mp.Queue()
        self.process = mp.Process(
            target=self._visualization_process,
            args=(self.viz_queue, width, height, title),
            daemon=True
        )
        self.process.start()
    
    def update(self, viz: Visualization) -> None:
        """Update the window with new visualization data."""
        try:
            self.viz_queue.put_nowait(viz)
        except:
            pass  # Skip frame if queue is full
    
    def close(self) -> None:
        """Close the window and clean up resources."""
        self.process.join()
    
    @staticmethod
    def _visualization_process(viz_queue: mp.Queue, width: int, height: int, title: str):
        """Process that handles visualization rendering."""
        # Create window state
        window_state = WindowState.create(
            width=width, height=height,
            title=title
        )
        
        # Create renderers
        gaussian_renderer = GaussianRenderer(window_state.device, window_state.format)
        arc_renderer = ArcRenderer(window_state.device, window_state.format)
        window_state.attach_renderer(gaussian_renderer)
        window_state.attach_renderer(arc_renderer)
        
        # Create visualization stream from queue
        viz_emitter = EventEmitter.from_queue(viz_queue)
        
        # Update renderers when new visualization arrives
        def on_viz(viz: Visualization):
            gaussian_renderer.update(viz.gaussians)
            arc_renderer.update(viz.arcs)
        
        # Subscribe to visualization updates
        viz_emitter.subscribe(on_viz)
        
        # Run the window
        window_state.game_loop() 