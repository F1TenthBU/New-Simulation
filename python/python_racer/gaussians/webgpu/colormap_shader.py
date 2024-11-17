import numpy as np
from matplotlib import colormaps

def generate_colormap_shader_code(colormap_name: str = 'inferno', samples: int = 1024, scale: float = 5.0) -> str:
    cmap = colormaps[colormap_name]
    x = np.linspace(0, 1, samples)
    colors = cmap(x)[:, :3]
    
    coeffs = []
    for i in range(3):
        coeff = np.polyfit(x, colors[:, i], 6)
        coeffs.append(coeff)
    
    coeff_lines = []
    for i in range(7):
        coeff_lines.append(f"    let c{i} = vec3f({coeffs[0][i]:e}f, {coeffs[1][i]:e}f, {coeffs[2][i]:e}f);")
    
    return f'''
struct VertexInput {{
    @location(0) position: vec2f,
    @location(1) texcoord: vec2f,
}};

struct VertexOutput {{
    @builtin(position) position: vec4f,
    @location(0) texcoord: vec2f,
}};

@group(0) @binding(0) var accumulation_texture: texture_2d<f32>;
@group(0) @binding(1) var texture_sampler: sampler;

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {{
    var out: VertexOutput;
    out.position = vec4f(in.position, 0.0, 1.0);
    out.texcoord = in.texcoord;
    return out;
}}

fn colormap(t: f32) -> vec3f {{
{chr(10).join(coeff_lines)}

    let t2 = t * t;
    let t3 = t2 * t;
    let t4 = t3 * t;
    let t5 = t4 * t;
    let t6 = t5 * t;

    return c6 + c5*t + c4*t2 + c3*t3 + c2*t4 + c1*t5 + c0*t6;
}}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4f {{
    let accumulated = textureSample(accumulation_texture, texture_sampler, in.texcoord).r;
    let scaled_value = clamp(accumulated / {scale}f, 0.0, 1.0);
    let color = colormap(scaled_value);
    return vec4f(color, 1.0);
}}
'''