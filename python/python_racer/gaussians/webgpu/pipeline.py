import wgpu
import numpy as np
from .gaussian_shader import GAUSSIAN_SHADER
from .arc_shader import ARC_SHADER
from .colormap_shader import generate_colormap_shader_code
from ..gaussians import Gaussians

def create_buffers(device: wgpu.GPUDevice, gaussians: Gaussians):
    """Create vertex and instance buffers."""
    # Create vertex buffers (exactly as in original)
    gaussian_vertices = np.array([
        # First triangle
        -4.0, -4.0,  -4.0, -4.0,
         4.0, -4.0,   4.0, -4.0,
         4.0,  4.0,   4.0,  4.0,
        # Second triangle
        -4.0, -4.0,  -4.0, -4.0,
         4.0,  4.0,   4.0,  4.0,
        -4.0,  4.0,  -4.0,  4.0,
    ], dtype=np.float32)
    
    fullscreen_vertices = np.array([
        # First triangle (fullscreen quad)
        -1.0, -1.0,   0.0, 1.0,
         3.0, -1.0,   2.0, 1.0,
        -1.0,  3.0,   0.0, -1.0,
    ], dtype=np.float32)
    
    # Create instance data with pre-allocation (exactly as in original)
    max_instances = 2_000_000
    instance_data = np.zeros(max_instances, dtype=np.dtype([
        ('pos', np.float32, 2),
        ('std', np.float32, 1),
        ('intensity', np.float32, 1),
    ]))
    instance_data['pos'][:len(gaussians.pos)] = gaussians.pos
    instance_data['std'][:len(gaussians.pos)] = gaussians.std
    instance_data['intensity'][:len(gaussians.pos)] = gaussians.intensity
    
    # Create buffers with create_buffer_with_data
    gaussian_vertex_buffer = device.create_buffer_with_data(
        data=gaussian_vertices,
        usage=wgpu.BufferUsage.VERTEX
    )
    
    fullscreen_vertex_buffer = device.create_buffer_with_data(
        data=fullscreen_vertices,
        usage=wgpu.BufferUsage.VERTEX
    )
    
    instance_buffer = device.create_buffer_with_data(
        data=instance_data,
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST
    )
    
    arc_buffer = device.create_buffer_with_data(
        data=np.zeros((1000, 2), dtype=np.float32),  # Pre-fill with zeros
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST
    )
    
    view_uniform_buffer = device.create_buffer(
        size=16,
        usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
    )
    
    return gaussian_vertex_buffer, fullscreen_vertex_buffer, instance_buffer, arc_buffer, view_uniform_buffer

def create_pipelines(device: wgpu.GPUDevice, format: wgpu.TextureFormat):
    """Create render pipelines."""
    # Create shaders
    accumulation_shader = device.create_shader_module(
        label="accumulation_shader",
        code=GAUSSIAN_SHADER
    )
    
    colormap_shader = device.create_shader_module(
        label="colormap_shader",
        code=generate_colormap_shader_code()
    )
    
    arc_shader = device.create_shader_module(
        label="arc_shader",
        code=ARC_SHADER
    )
    
    # Create bind group layouts
    view_bind_group_layout = device.create_bind_group_layout(
        entries=[{
            "binding": 0,
            "visibility": wgpu.ShaderStage.VERTEX,
            "buffer": {"type": "uniform"}
        }]
    )
    
    colormap_bind_group_layout = device.create_bind_group_layout(
        entries=[
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {
                    "sample_type": wgpu.TextureSampleType.float,
                    "view_dimension": wgpu.TextureViewDimension.d2
                }
            },
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "sampler": {"type": wgpu.SamplerBindingType.filtering}
            }
        ]
    )
    
    # Create accumulation pipeline (unchanged from original)
    accumulation_pipeline = device.create_render_pipeline(
        label="accumulation_pipeline",
        layout=device.create_pipeline_layout(
            bind_group_layouts=[view_bind_group_layout]
        ),
        vertex={
            "module": accumulation_shader,
            "entry_point": "vs_main",
            "buffers": [
                {  # Vertex buffer
                    "array_stride": 16,
                    "attributes": [
                        {"format": wgpu.VertexFormat.float32x2, "offset": 0, "shader_location": 0},
                        {"format": wgpu.VertexFormat.float32x2, "offset": 8, "shader_location": 1}
                    ]
                },
                {  # Instance buffer
                    "array_stride": 16,
                    "step_mode": wgpu.VertexStepMode.instance,
                    "attributes": [
                        {"format": wgpu.VertexFormat.float32x2, "offset": 0, "shader_location": 2},
                        {"format": wgpu.VertexFormat.float32, "offset": 8, "shader_location": 3},
                        {"format": wgpu.VertexFormat.float32, "offset": 12, "shader_location": 4}
                    ]
                }
            ]
        },
        fragment={
            "module": accumulation_shader,
            "entry_point": "fs_main",
            "targets": [{
                "format": wgpu.TextureFormat.r16float,
                "blend": {
                    "color": {
                        "src_factor": wgpu.BlendFactor.one,
                        "dst_factor": wgpu.BlendFactor.one,
                        "operation": wgpu.BlendOperation.add
                    },
                    "alpha": {
                        "src_factor": wgpu.BlendFactor.one,
                        "dst_factor": wgpu.BlendFactor.one,
                        "operation": wgpu.BlendOperation.add
                    }
                }
            }]
        },
        primitive={
            "topology": wgpu.PrimitiveTopology.triangle_list,
            "front_face": wgpu.FrontFace.ccw,
            "cull_mode": wgpu.CullMode.none
        }
    )
    
    # Create colormap pipeline (unchanged from original)
    colormap_pipeline = device.create_render_pipeline(
        label="colormap_pipeline",
        layout=device.create_pipeline_layout(
            bind_group_layouts=[colormap_bind_group_layout]
        ),
        vertex={
            "module": colormap_shader,
            "entry_point": "vs_main",
            "buffers": [{
                "array_stride": 16,
                "attributes": [
                    {"format": wgpu.VertexFormat.float32x2, "offset": 0, "shader_location": 0},
                    {"format": wgpu.VertexFormat.float32x2, "offset": 8, "shader_location": 1}
                ]
            }]
        },
        fragment={
            "module": colormap_shader,
            "entry_point": "fs_main",
            "targets": [{
                "format": format
            }]
        },
        primitive={
            "topology": wgpu.PrimitiveTopology.triangle_list,
            "front_face": wgpu.FrontFace.ccw,
            "cull_mode": wgpu.CullMode.none
        }
    )
    
    # Create arc pipeline
    arc_pipeline = device.create_render_pipeline(
        label="arc_pipeline",
        layout=device.create_pipeline_layout(
            bind_group_layouts=[view_bind_group_layout]
        ),
        vertex={
            "module": arc_shader,
            "entry_point": "vs_main",
            "buffers": [{
                "array_stride": 8,
                "attributes": [
                    {"format": wgpu.VertexFormat.float32x2, "offset": 0, "shader_location": 0}
                ]
            }]
        },
        fragment={
            "module": arc_shader,
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
            "topology": wgpu.PrimitiveTopology.line_strip,
            "strip_index_format": wgpu.IndexFormat.uint32
        }
    )
    
    return accumulation_pipeline, colormap_pipeline, arc_pipeline, view_bind_group_layout, colormap_bind_group_layout