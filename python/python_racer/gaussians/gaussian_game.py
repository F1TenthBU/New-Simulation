from dataclasses import dataclass, replace
from typing import Optional
import numpy as np
import wgpu
from wgpu.gui.auto import WgpuCanvas
import glfw
import time

from .game_engine import SceneState, WindowConfig, GameEngine
from .view_transform import ViewTransform
from .gaussians import Gaussians
from .webgpu.pipeline import create_pipelines, create_buffers

@dataclass(frozen=True)
class Arc:
    """Arc data for visualization."""
    points: np.ndarray  # shape: (num_points, 2)
    color: np.ndarray   # shape: (4,) RGBA

@dataclass(frozen=True)
class GameState(SceneState):
    """Main game state handling gaussian rendering and interaction."""
    view: ViewTransform
    gaussians: Gaussians
    device: wgpu.GPUDevice
    accumulation_pipeline: wgpu.GPURenderPipeline
    colormap_pipeline: wgpu.GPURenderPipeline
    arc_pipeline: wgpu.GPURenderPipeline
    bind_group: wgpu.GPUBindGroup
    gaussian_vertex_buffer: wgpu.GPUBuffer
    fullscreen_vertex_buffer: wgpu.GPUBuffer
    instance_buffer: wgpu.GPUBuffer
    arc_buffer: wgpu.GPUBuffer
    view_uniform_buffer: wgpu.GPUBuffer
    colormap_bind_group_layout: wgpu.GPUBindGroupLayout
    mouse_pos: Optional[np.ndarray] = None
    last_placed_pos: Optional[np.ndarray] = None
    arc: Optional[Arc] = None

    @staticmethod
    def create(width: int, height: int, canvas: WgpuCanvas, device: wgpu.GPUDevice) -> 'GameState':
        """Create initial game state with graphics resources."""
        context = canvas.get_context()
        format = context.get_preferred_format(device.adapter)
        context.configure(device=device, format=format, alpha_mode="opaque")
        
        # Create initial gaussians
        gaussians = Gaussians(
            pos=np.zeros((0, 2), dtype=np.float32),
            std=np.array([], dtype=np.float32),
            intensity=np.array([], dtype=np.float32)
        )
        
        # Create graphics pipelines and buffers
        accumulation_pipeline, colormap_pipeline, arc_pipeline, view_bind_group_layout, colormap_bind_group_layout = create_pipelines(device, format)
        gaussian_vertex_buffer, fullscreen_vertex_buffer, instance_buffer, arc_buffer, view_uniform_buffer = create_buffers(device, gaussians)
        
        # Create view bind group
        bind_group = device.create_bind_group(
            layout=view_bind_group_layout,
            entries=[{
                "binding": 0,
                "resource": {"buffer": view_uniform_buffer}
            }]
        )

        return GameState(
            view=ViewTransform.create(width, height),
            gaussians=gaussians,
            device=device,
            accumulation_pipeline=accumulation_pipeline,
            colormap_pipeline=colormap_pipeline,
            arc_pipeline=arc_pipeline,
            bind_group=bind_group,
            gaussian_vertex_buffer=gaussian_vertex_buffer,
            fullscreen_vertex_buffer=fullscreen_vertex_buffer,
            instance_buffer=instance_buffer,
            arc_buffer=arc_buffer,
            view_uniform_buffer=view_uniform_buffer,
            colormap_bind_group_layout=colormap_bind_group_layout
        )

    def update_lidar(self, lidar_samples: np.ndarray, sigma: float = 1.0) -> Optional['GameState']:
        """Update visualization with new LIDAR data."""
        if lidar_samples is None:
            return None

        # Convert LIDAR to gaussians
        num_samples = len(lidar_samples)
        angles = np.linspace(0, 2 * np.pi, num_samples)
        valid_samples = lidar_samples > 0

        # Convert polar to cartesian coordinates
        x = lidar_samples[valid_samples] * np.sin(angles[valid_samples])
        y = lidar_samples[valid_samples] * np.cos(angles[valid_samples])
        positions = np.column_stack([x, y])

        new_gaussians = Gaussians(
            pos=positions.astype(np.float32),
            std=np.full(len(positions), sigma, dtype=np.float32),
            intensity=np.ones(len(positions), dtype=np.float32)
        )

        return replace(self, gaussians=new_gaussians)

    def update_arc(self, arc: Optional[Arc]) -> 'GameState':
        """Update the arc data."""
        if arc is not None:
            self.device.queue.write_buffer(self.arc_buffer, 0, arc.points.tobytes())
        return replace(self, arc=arc)

    def render(self, canvas: WgpuCanvas) -> None:
        """Render the current state."""
        try:
            current_texture = canvas.get_context().get_current_texture()
        except RuntimeError as e:
            if "Cannot get surface texture (2)" in str(e):
                return
            raise
            
        # Create intermediate texture for accumulation
        width, height = current_texture.width, current_texture.height
        accumulation_texture = self.device.create_texture(
            size={"width": width, "height": height, "depth_or_array_layers": 1},
            format=wgpu.TextureFormat.r16float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        )
            
        # Update instance data - use same size as pre-allocated buffer
        max_instances = 2_000_000
        instance_data = np.zeros(max_instances, dtype=np.dtype([
            ('pos', np.float32, 2),
            ('std', np.float32, 1),
            ('intensity', np.float32, 1),
        ]))
        
        # Fill with actual data
        instance_data['pos'][:len(self.gaussians.pos)] = self.gaussians.pos
        instance_data['std'][:len(self.gaussians.pos)] = self.gaussians.std
        instance_data['intensity'][:len(self.gaussians.pos)] = self.gaussians.intensity
        
        # Update buffers
        self.device.queue.write_buffer(self.instance_buffer, 0, instance_data.tobytes())
        self.device.queue.write_buffer(
            self.view_uniform_buffer, 
            0, 
            np.array([*self.view.world_rect.center, self.view.world_rect.width, self.view.world_rect.height], dtype=np.float32).tobytes()
        )
        
        # First pass: accumulate gaussians
        command_encoder = self.device.create_command_encoder()
        render_pass = command_encoder.begin_render_pass(
            color_attachments=[{
                "view": accumulation_texture.create_view(),
                "clear_value": (0.0, 0.0, 0.0, 1.0),
                "load_op": wgpu.LoadOp.clear,
                "store_op": wgpu.StoreOp.store,
            }]
        )
        
        render_pass.set_pipeline(self.accumulation_pipeline)
        render_pass.set_bind_group(0, self.bind_group)
        render_pass.set_vertex_buffer(0, self.gaussian_vertex_buffer)
        render_pass.set_vertex_buffer(1, self.instance_buffer)
        render_pass.draw(6, len(self.gaussians.pos))
        render_pass.end()
        
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
        render_pass = command_encoder.begin_render_pass(
            color_attachments=[{
                "view": current_texture.create_view(),
                "clear_value": (0.0, 0.0, 0.0, 1.0),
                "load_op": wgpu.LoadOp.clear,
                "store_op": wgpu.StoreOp.store,
            }]
        )
        
        render_pass.set_pipeline(self.colormap_pipeline)
        render_pass.set_bind_group(0, colormap_bind_group)
        render_pass.set_vertex_buffer(0, self.fullscreen_vertex_buffer)
        render_pass.draw(3, 1)
        render_pass.end()
        
        # Third pass: render arc
        if self.arc is not None:
            render_pass = command_encoder.begin_render_pass(
                color_attachments=[{
                    "view": current_texture.create_view(),
                    "load_op": wgpu.LoadOp.load,  # Don't clear
                    "store_op": wgpu.StoreOp.store,
                }]
            )
            render_pass.set_pipeline(self.arc_pipeline)
            render_pass.set_bind_group(0, self.bind_group)  # Use same view transform
            render_pass.set_vertex_buffer(0, self.arc_buffer)
            render_pass.draw(len(self.arc.points), 1)
            render_pass.end()
        
        self.device.queue.submit([command_encoder.finish()])

    def handle_event(self, window: int, scroll_offset: tuple[float, float]) -> Optional['GameState']:
        """Handle user input for camera control."""
        mouse_screen_pos = np.array(glfw.get_cursor_pos(window))
        mouse_world_pos = self.view.screen_to_world(mouse_screen_pos)
        left_pressed = glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS

        # Update view transform
        new_view = self.view.handle_event(scroll_offset, mouse_screen_pos, left_pressed)
        if new_view is not None:
            return replace(self, view=new_view)

        # Update mouse position
        if mouse_world_pos is not None and not np.array_equal(mouse_world_pos, self.mouse_pos):
            return replace(self, mouse_pos=mouse_world_pos)

        return None

if __name__ == "__main__":
    config = WindowConfig(
        width=1024,
        height=768,
        title="Gaussian Game"
    )
    
    engine = GameEngine.create(config)
    game_state = GameState.create(config.width, config.height, engine.canvas, engine.device)
    engine.run(game_state)