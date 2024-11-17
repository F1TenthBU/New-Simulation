import glfw
import wgpu
from wgpu.gui.auto import WgpuCanvas, run
import os

def main():
    # Force X11 before anything else
    os.environ["DISPLAY"] = ":0"
    os.environ["XDG_SESSION_TYPE"] = "x11"
    if "WAYLAND_DISPLAY" in os.environ:
        del os.environ["WAYLAND_DISPLAY"]
    
    # Initialize GLFW
    if not glfw.init():
        return
    print("GLFW initialized")
    
    # Create canvas (this handles surface creation)
    canvas = WgpuCanvas(
        size=(640, 480),
        title="Test"
    )
    print("Canvas created")
    
    # Get adapter and device
    adapter = wgpu.gpu.request_adapter_sync(
        power_preference="high-performance"
    )
    device = adapter.request_device_sync()
    print("Got adapter and device")
    
    # Configure canvas
    context = canvas.get_context()
    format = context.get_preferred_format(adapter)
    context.configure(
        device=device,
        format=format,
        alpha_mode="opaque",
    )
    print("Canvas configured")
    
    # Create shader
    shader = device.create_shader_module(
        label="triangle",
        code="""
        @vertex
        fn vs_main(@builtin(vertex_index) idx: u32) -> @builtin(position) vec4f {
            var pos = array(
                vec2f( 0.0,  0.5),
                vec2f(-0.5, -0.5),
                vec2f( 0.5, -0.5)
            );
            return vec4f(pos[idx], 0.0, 1.0);
        }

        @fragment
        fn fs_main() -> @location(0) vec4f {
            return vec4f(1.0, 0.0, 0.0, 1.0);  // Red triangle
        }
        """
    )
    print("Created shader")
    
    # Create pipeline
    pipeline = device.create_render_pipeline(
        label="triangle",
        layout="auto",
        vertex={
            "module": shader,
            "entry_point": "vs_main",
        },
        fragment={
            "module": shader,
            "entry_point": "fs_main",
            "targets": [{
                "format": format,
            }],
        },
    )
    print("Created pipeline")
    
    def frame():
        current_texture = canvas.get_context().get_current_texture()
        command_encoder = device.create_command_encoder()
        
        render_pass = command_encoder.begin_render_pass(
            color_attachments=[{
                "view": current_texture.create_view(),
                "clear_value": (0.1, 0.1, 0.1, 1.0),  # Dark gray background
                "load_op": wgpu.LoadOp.clear,
                "store_op": wgpu.StoreOp.store,
            }]
        )
        
        render_pass.set_pipeline(pipeline)
        render_pass.draw(3, 1, 0, 0)
        render_pass.end()
        
        device.queue.submit([command_encoder.finish()])
        canvas.request_draw(frame)
    
    canvas.request_draw(frame)
    run()

if __name__ == "__main__":
    main() 