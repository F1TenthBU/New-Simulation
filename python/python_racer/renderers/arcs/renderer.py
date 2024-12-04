from dataclasses import dataclass
import numpy as np
import wgpu
from wgpu.gui.auto import WgpuCanvas
from typing import List

from python_racer.events.window_events import RenderEvent
from .pipeline import create_arc_pipeline, create_buffers
from python_racer.types.geometry import Arc, Rectangle
from python_racer.renderers.base import Renderer


def normalize(vectors: np.ndarray) -> np.ndarray:
    """Normalize vectors along last axis."""
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)  # Avoid division by zero
    return vectors / norms

class ArcRenderer(Renderer):
    """Renderer for trajectory arcs."""
    
    def __init__(self, device: wgpu.GPUDevice, format: wgpu.TextureFormat):
        print("Initializing ArcRenderer")
        self.device = device
        
        # Create pipeline and get layouts
        self.pipeline, self.bind_group_layout = create_arc_pipeline(device, format)
        
        # Create vertex buffer for a line segment (4 vertices for a strip)
        vertices = np.array([
            [-0.5, -1.0],  # Bottom start
            [-0.5,  1.0],  # Top start
            [ 0.5, -1.0],  # Bottom end
            [ 0.5,  1.0],  # Top end
        ], dtype=np.float32)
        
        # Pre-calculate max segments based on expected usage
        MAX_SEGMENTS = 1000 * 100  # 100 segments per curve, 1000 curves
        INSTANCE_STRIDE = 52  # 13 floats per instance
        
        # Create the vertex buffer
        self.vertex_buffer = device.create_buffer(
            size=vertices.nbytes,
            usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
        )
        self.device.queue.write_buffer(self.vertex_buffer, 0, vertices.tobytes())
        
        # Create optimized instance buffer
        self.instance_buffer = device.create_buffer(
            size=MAX_SEGMENTS * INSTANCE_STRIDE,
            usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
        )
        
        self.view_uniform_buffer = device.create_buffer(
            size=16,  # vec2f center + vec2f size
            usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
        )
        
        # Initialize view uniform buffer with default values
        initial_view_data = np.array([0.0, 0.0, 100.0, 100.0], dtype=np.float32)
        self.device.queue.write_buffer(self.view_uniform_buffer, 0, initial_view_data.tobytes())
        
        # Create bind group
        self.bind_group = device.create_bind_group(
            layout=self.bind_group_layout,
            entries=[{
                "binding": 0,
                "resource": {"buffer": self.view_uniform_buffer}
            }]
        )
        
        # Initialize empty arcs list and instance count
        self.arcs: List[Arc] = []
        self.num_instances = 0
        
        # Track pending updates
        self.pending_arcs = None
        self.pending_view = None
    
    def write_arcs(self, arcs: List[Arc]) -> None:
        """Write arc data to instance buffer."""
        if not arcs:
            self.arcs = []
            self.num_instances = 0
            return
        
        self.arcs = arcs
        
        # Pre-calculate total segments needed
        total_segments = sum(len(arc.points) - 1 for arc in arcs)
        instance_data = np.zeros((total_segments, 13), dtype=np.float32)
        
        current_idx = 0
        for arc in arcs:
            points = arc.points
            n_segments = len(points) - 1
            if n_segments <= 0:
                continue
                
            # Get all points and calculate segments vectorized
            segment_starts = points[:-1]  # All start points
            segment_ends = points[1:]     # All end points
            
            # Calculate directions using vectorized operations
            segments = segment_ends - segment_starts
            directions = normalize(segments)
            
            # Calculate start and end directions for each segment
            prev_dirs = np.roll(directions, 1, axis=0)
            next_dirs = np.roll(directions, -1, axis=0)
            
            # Handle first and last segments
            prev_dirs[0] = directions[0]
            next_dirs[-1] = directions[-1]
            
            # Calculate tangent directions
            start_dirs = normalize(directions + prev_dirs)
            end_dirs = normalize(directions + next_dirs)
            
            # Fill instance data efficiently
            end_idx = current_idx + n_segments
            instance_data[current_idx:end_idx, 0:2] = segment_starts
            instance_data[current_idx:end_idx, 2:4] = segment_ends
            instance_data[current_idx:end_idx, 4:6] = start_dirs
            instance_data[current_idx:end_idx, 6:8] = end_dirs
            instance_data[current_idx:end_idx, 8:12] = arc.color
            instance_data[current_idx:end_idx, 12] = arc.width
            
            current_idx = end_idx
        
        # Single buffer update
        if current_idx > 0:
            self.device.queue.write_buffer(self.instance_buffer, 0, instance_data[:current_idx].tobytes())
            self.num_instances = current_idx
        else:
            self.num_instances = 0
    
    def write_view(self, rect: Rectangle) -> None:
        """Write view data to uniform buffer."""
        data = np.array([
            rect.center[0], rect.center[1],
            rect.size[0], rect.size[1]
        ], dtype=np.float32)
        self.device.queue.write_buffer(self.view_uniform_buffer, 0, data.tobytes())
    
    def update(self, arcs: List[Arc]) -> None:
        """Queue arc update for next render."""
        self.pending_arcs = arcs
    
    def update_view_uniforms(self, rect: Rectangle) -> None:
        """Queue view update for next render."""
        self.pending_view = rect

    def render(self, event: RenderEvent) -> None:
        """Render all arcs using instanced rendering."""
        try:
            # Apply any pending updates in render thread
            if self.pending_arcs is not None:
                self.write_arcs(self.pending_arcs)
                self.pending_arcs = None
            
            if self.pending_view is not None:
                self.write_view(self.pending_view)
                self.pending_view = None
            
            current_texture = event.canvas.get_context().get_current_texture()
        except RuntimeError as e:
            if "Cannot get surface texture" in str(e):
                return
            raise
            
        # Create render pass
        render_pass = event.command_encoder.begin_render_pass(
            color_attachments=[{
                "view": current_texture.create_view(),
                "load_op": wgpu.LoadOp.load,  # Load existing content
                "store_op": wgpu.StoreOp.store,
            }]
        )
        
        render_pass.set_pipeline(self.pipeline)
        render_pass.set_bind_group(0, self.bind_group)
        render_pass.set_vertex_buffer(0, self.vertex_buffer)
        render_pass.set_vertex_buffer(1, self.instance_buffer)
        render_pass.draw(4, self.num_instances)
        render_pass.end()