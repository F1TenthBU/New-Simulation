from textwrap import dedent

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