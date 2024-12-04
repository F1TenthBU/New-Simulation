import numpy as np
from matplotlib import colormaps

GAUSSIAN_SHADER = '''
struct VertexInput {
    @location(0) position: vec2f,
    @location(1) texcoord: vec2f,
    @location(2) instance_pos: vec2f,
    @location(3) instance_stddev: f32,
    @location(4) instance_intensity: f32,
};

struct ViewUniform {
    world_center: vec2f,
    world_size: vec2f,
};
@group(0) @binding(0) var<uniform> view: ViewUniform;

struct VertexOutput {
    @builtin(position) position: vec4f,
    @location(0) texcoord: vec2f,
    @location(1) stddev: f32,
    @location(2) intensity: f32,
};

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
    var out: VertexOutput;
    
    // Convert to screen space
    let screen_pos = (in.instance_pos - view.world_center) / (view.world_size * 0.5);
    
    // Scale gaussian size uniformly relative to world size
    let base_scale = 4.0 * in.instance_stddev;
    let scaled_pos = screen_pos + in.position * base_scale / view.world_size;
    
    out.position = vec4f(scaled_pos, 0.0, 1.0);
    out.texcoord = in.texcoord;
    out.stddev = in.instance_stddev;
    out.intensity = in.instance_intensity;
    return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) f32 {
    let sq_dist = dot(in.texcoord, in.texcoord);
    return in.intensity * exp(-0.5 * sq_dist);
}
'''

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
    return vec4f(color, scaled_value);
}}
'''
# Generate colormap shader with inferno colormap
COLORMAP_SHADER = generate_colormap_shader_code(colormap_name='inferno', samples=1024, scale=5.0) 