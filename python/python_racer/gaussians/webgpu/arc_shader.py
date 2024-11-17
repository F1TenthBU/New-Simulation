ARC_SHADER = '''
struct VertexInput {
    @location(0) position: vec2f,
};

struct ViewUniform {
    world_center: vec2f,
    world_size: vec2f,
};
@group(0) @binding(0) var<uniform> view: ViewUniform;

@vertex
fn vs_main(in: VertexInput) -> @builtin(position) vec4f {
    let screen_pos = (in.position - view.world_center) / (view.world_size * 0.5);
    return vec4f(screen_pos, 0.0, 1.0);
}

@fragment
fn fs_main() -> @location(0) vec4f {
    return vec4f(0.0, 1.0, 0.0, 0.8);  // Semi-transparent green
}
''' 