import wgpu
import numpy as np
from .shader import ARC_SHADER

def create_arc_pipeline(device: wgpu.GPUDevice, format: wgpu.TextureFormat):
    """
    Create render pipeline for arc visualization.
    
    Args:
        device: WebGPU device
        format: Texture format for rendering
        
    Returns:
        Tuple of (pipeline, bind_group_layout)
    """
    # Create shader module
    shader = device.create_shader_module(
        label="arc_shader",
        code=ARC_SHADER
    )
    
    # Create bind group layout for view transform
    bind_group_layout = device.create_bind_group_layout(
        entries=[{
            "binding": 0,
            "visibility": wgpu.ShaderStage.VERTEX,
            "buffer": {"type": "uniform"}
        }]
    )
    
    # Create pipeline
    pipeline = device.create_render_pipeline(
        label="arc_pipeline",
        layout=device.create_pipeline_layout(
            bind_group_layouts=[bind_group_layout]
        ),
        vertex={
            "module": shader,
            "entry_point": "vs_main",
            "buffers": [
                {  # Vertex buffer - quad vertices
                    "array_stride": 8,  # 2 floats (x,y)
                    "step_mode": wgpu.VertexStepMode.vertex,
                    "attributes": [
                        {"format": wgpu.VertexFormat.float32x2, "offset": 0, "shader_location": 0}
                    ]
                },
                {  # Instance buffer - per-segment data
                    "array_stride": 52,  # 13 floats total
                    "step_mode": wgpu.VertexStepMode.instance,
                    "attributes": [
                        {"format": wgpu.VertexFormat.float32x2, "offset": 0, "shader_location": 1},   # start
                        {"format": wgpu.VertexFormat.float32x2, "offset": 8, "shader_location": 2},   # end
                        {"format": wgpu.VertexFormat.float32x2, "offset": 16, "shader_location": 3},  # start_dir
                        {"format": wgpu.VertexFormat.float32x2, "offset": 24, "shader_location": 4},  # end_dir
                        {"format": wgpu.VertexFormat.float32x4, "offset": 32, "shader_location": 5},  # color
                        {"format": wgpu.VertexFormat.float32, "offset": 48, "shader_location": 6},    # width
                    ]
                }
            ]
        },
        fragment={
            "module": shader,
            "entry_point": "fs_main",
            "targets": [{
                "format": format,
                "blend": {
                    "color": {
                        "src_factor": wgpu.BlendFactor.src_alpha,
                        "dst_factor": wgpu.BlendFactor.one_minus_src_alpha,
                        "operation": wgpu.BlendOperation.add
                    },
                    "alpha": {
                        "src_factor": wgpu.BlendFactor.one,
                        "dst_factor": wgpu.BlendFactor.one_minus_src_alpha,
                        "operation": wgpu.BlendOperation.add
                    }
                }
            }]
        },
        primitive={
            "topology": wgpu.PrimitiveTopology.triangle_strip,
            "front_face": wgpu.FrontFace.ccw,
            "cull_mode": wgpu.CullMode.none
        }
    )
    
    return pipeline, bind_group_layout

def create_buffers(device: wgpu.GPUDevice):
    """Create buffers for arc rendering."""
    # Create view uniform buffer
    view_uniform_buffer = device.create_buffer(
        size=16,  # vec2f center + vec2f size
        usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
    )
    
    return view_uniform_buffer 