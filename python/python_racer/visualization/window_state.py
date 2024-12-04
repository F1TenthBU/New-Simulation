"""Window state that emits events."""
from dataclasses import dataclass, field
import numpy as np
import wgpu
from wgpu.gui.auto import WgpuCanvas, run
import os
import platform

from python_racer.events.emitter import EventEmitter
from python_racer.types.geometry import Rectangle
from ..events.window_events import RenderEvent, WindowEvents, WindowResizeEvent, MouseMoveEvent, MouseDragEvent, ScrollEvent
import time
from python_racer.renderers.base import Renderer
from python_racer.visualization.view_transform import create_world_rect_stream

@dataclass
class WindowState:
    """Handles window creation, events, and game loop."""
    canvas: wgpu.WgpuCanvasInterface
    device: wgpu.GPUDevice
    adapter: wgpu.GPUAdapter
    format: wgpu.TextureFormat
    events: WindowEvents
    _world_rect: EventEmitter[Rectangle]
    _last_pos: np.ndarray = np.array([0.0, 0.0], dtype=np.float32)
    _drag_start: np.ndarray = np.array([0.0, 0.0], dtype=np.float32)
    _current_size: tuple[int, int] = (0, 0)
    _last_frame_time: float = field(default_factory=lambda: time.time())
    
    @staticmethod
    def create(width: int, height: int, title: str) -> 'WindowState':
        """Create window and initialize graphics."""
        if platform.system() == "Linux":
            os.environ["DISPLAY"] = ":0"
            os.environ["XDG_SESSION_TYPE"] = "x11"
            if "WAYLAND_DISPLAY" in os.environ:
                del os.environ["WAYLAND_DISPLAY"]
        
        # Create canvas with high refresh rate
        canvas = WgpuCanvas(
            size=(width, height), 
            title=title,
            max_fps=240  # Allow higher refresh rates
        )
        adapter = wgpu.gpu.request_adapter_sync()
        device = adapter.request_device_sync()
        
        # Configure context
        context = canvas.get_context()
        format = context.get_preferred_format(adapter)
        context.configure(device=device, format=format, alpha_mode="opaque")
        
        events = WindowEvents(window=canvas._window)
        
        # Create world rect stream during initialization
        world_rect = create_world_rect_stream(
            initial_size=(width, height),
            events=events,
            initial_world_height=50.0
        )
        
        window_state = WindowState(
            canvas=canvas, 
            device=device, 
            adapter=adapter, 
            format=format, 
            events=events,
            _world_rect=world_rect,
            _current_size=(width, height),
        )
        
        @canvas.add_event_handler("pointer_move")
        def on_pointer_move(event):
            # Use current size from resize events
            width, height = window_state._current_size
            pos = np.array([
                event['x'] / width,
                1.0 - (event['y'] / height)  # Flip Y coordinate
            ], dtype=np.float32)
            
            events.mouse_move.emit(MouseMoveEvent(pos))
            
            if 1 in event['buttons']:  # Left button in buttons list
                events.mouse_drag.emit(MouseDragEvent(
                    start=window_state._drag_start,
                    current=pos,
                    delta=pos - window_state._last_pos
                ))
            window_state._last_pos = pos
        
        @canvas.add_event_handler("pointer_down")
        def on_pointer_down(event):
            if event['button'] == 1:  # Left button according to docs
                window_state._drag_start = window_state._last_pos
        
        @canvas.add_event_handler("wheel")
        def on_wheel(event):
            events.scroll.emit(ScrollEvent((event['dx'], event['dy'])))
        
        @canvas.add_event_handler("resize")
        def on_resize(event):
            width = event['width']
            height = event['height']
            previous_size = window_state._current_size
            window_state._current_size = (width, height)
            print(f"[WindowState] Resize: {width}x{height} (ratio: {event['pixel_ratio']})")
            events.resize.emit(WindowResizeEvent(
                size=np.array([width, height], dtype=np.float32),
                previous_size=np.array(previous_size, dtype=np.float32)
            ))
        
        return window_state
    
    def game_loop(self) -> None:
        # Track frame time
        last_time = time.time()
        
        def frame():
            nonlocal last_time
            
            # Calculate and print FPS
            current_time = time.time()
            fps = 1.0 / (current_time - last_time)
            last_time = current_time
            # print(f"\rFPS: {fps:.1f}", end="", flush=True)
            
            try:
                # Get current texture
                command_encoder = self.device.create_command_encoder()
                
                # Pass dt in RenderEvent without creating render pass
                self.events.render.emit(RenderEvent(
                    command_encoder=command_encoder, 
                    canvas=self.canvas,
                    dt=1.0/fps
                ))
                
                # Submit commands
                self.device.queue.submit([command_encoder.finish()])
            
            except RuntimeError as e:
                if "Cannot get surface texture" in str(e):
                    self.canvas.request_draw(frame)
                    return
                raise
            
            self.canvas.request_draw(frame)
        
        self.canvas.request_draw(frame)
        run()
        
    def attach_renderer(self, renderer: Renderer) -> None:
        """
        Attach a renderer to the window state.
        Subscribes the renderer to render events and view transform updates.
        """
        self.events.render.subscribe(renderer.render)
        self._world_rect.subscribe(renderer.update_view_uniforms)
        

        
    