from dataclasses import dataclass
import numpy as np
import wgpu

from python_racer.types.geometry import Gaussians
from .pipeline import create_gaussian_pipeline, create_buffers
from ...events.window_events import RenderEvent
from ...types.geometry import Rectangle
from python_racer.renderers.base import Renderer

class GaussianRenderer(Renderer):
    """Renderer for gaussian point clouds."""
    
    def __init__(self, device: wgpu.GPUDevice, format: wgpu.TextureFormat):
        self.device = device
        
        # Create pipelines and resources
        (self.accumulation_pipeline, self.colormap_pipeline, 
         self.view_bind_group_layout, self.colormap_bind_group_layout) = create_gaussian_pipeline(device, format)
        
        # Create initial empty gaussians
        self.gaussians = Gaussians(
            pos=np.zeros((0, 2), dtype=np.float32),
            std=np.array([], dtype=np.float32),
            intensity=np.array([], dtype=np.float32)
        )
        
        # Create buffers
        (self.gaussian_vertex_buffer, self.fullscreen_vertex_buffer, 
         self.instance_buffer, self.view_uniform_buffer) = create_buffers(device, self.gaussians)
        
        # Create view bind group
        self.bind_group = device.create_bind_group(
            layout=self.view_bind_group_layout,
            entries=[{
                "binding": 0,
                "resource": {"buffer": self.view_uniform_buffer}
            }]
        )
        
        # Pre-allocate instance data buffer
        self.instance_data = np.zeros(2_000_000, dtype=np.dtype([
            ('pos', np.float32, 2),
            ('std', np.float32, 1),
            ('intensity', np.float32, 1),
        ]))
        
        # Track pending updates
        self.pending_gaussians = None
        self.pending_view = None
    
    def write_gaussians(self, gaussians: Gaussians) -> None:
        """Write gaussian data to instance buffer."""
        self.gaussians = gaussians
        self.instance_data['pos'][:len(self.gaussians.pos)] = self.gaussians.pos
        self.instance_data['std'][:len(self.gaussians.pos)] = self.gaussians.std
        self.instance_data['intensity'][:len(self.gaussians.pos)] = self.gaussians.intensity
        self.device.queue.write_buffer(self.instance_buffer, 0, self.instance_data.tobytes())
    
    def write_view(self, rect: Rectangle) -> None:
        """Write view data to uniform buffer."""
        data = np.array([
            rect.center[0], rect.center[1],
            rect.size[0], rect.size[1]
        ], dtype=np.float32)
        self.device.queue.write_buffer(self.view_uniform_buffer, 0, data.tobytes())
    
    def update_view_uniforms(self, rect: Rectangle) -> None:
        """Queue view update for next render."""
        self.pending_view = rect
    
    def update(self, gaussians: Gaussians) -> None:
        """Queue gaussian update for next render."""
        self.pending_gaussians = gaussians
    
    def render(self, event: RenderEvent) -> None:
        """Render gaussians using two-pass accumulation."""
        try:
            # Apply any pending updates in render thread
            if self.pending_gaussians is not None:
                self.write_gaussians(self.pending_gaussians)
                self.pending_gaussians = None
            
            if self.pending_view is not None:
                self.write_view(self.pending_view)
                self.pending_view = None
            
            current_texture = event.canvas.get_context().get_current_texture()
        except RuntimeError as e:
            if "Cannot get surface texture" in str(e):
                return
            raise
            
        width, height = current_texture.width, current_texture.height
        
        # Create intermediate texture for accumulation
        accumulation_texture = self.device.create_texture(
            size={"width": width, "height": height, "depth_or_array_layers": 1},
            format=wgpu.TextureFormat.r16float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        )
        
        # First pass: accumulate gaussians to intermediate texture
        first_pass = event.command_encoder.begin_render_pass(
            color_attachments=[{
                "view": accumulation_texture.create_view(),
                "clear_value": (0.0, 0.0, 0.0, 1.0),  # Clear intermediate texture
                "load_op": wgpu.LoadOp.clear,
                "store_op": wgpu.StoreOp.store,
            }]
        )
        
        first_pass.set_pipeline(self.accumulation_pipeline)
        first_pass.set_bind_group(0, self.bind_group)
        first_pass.set_vertex_buffer(0, self.gaussian_vertex_buffer)
        first_pass.set_vertex_buffer(1, self.instance_buffer)
        first_pass.draw(6, len(self.gaussians.pos))
        first_pass.end()
        
        # Create sampler and bind group for colormap
        sampler = self.device.create_sampler(
            min_filter="linear",
            mag_filter="linear",
            mipmap_filter="linear",
        )
        
        colormap_bind_group = self.device.create_bind_group(
            layout=self.colormap_bind_group_layout,
            entries=[
                {
                    "binding": 0,
                    "resource": accumulation_texture.create_view()
                },
                {
                    "binding": 1,
                    "resource": sampler
                }
            ]
        )
        
        # Second pass: apply colormap
        second_pass = event.command_encoder.begin_render_pass(
            color_attachments=[{
                "view": current_texture.create_view(),
                "load_op": wgpu.LoadOp.load,  # Load existing content
                "store_op": wgpu.StoreOp.store,
            }]
        )
        
        second_pass.set_pipeline(self.colormap_pipeline)
        second_pass.set_bind_group(0, colormap_bind_group)
        second_pass.set_vertex_buffer(0, self.fullscreen_vertex_buffer)
        second_pass.draw(3, 1)  # Draw fullscreen triangle
        second_pass.end()