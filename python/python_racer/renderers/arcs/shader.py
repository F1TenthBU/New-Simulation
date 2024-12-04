"""Shader code for rendering smooth, thick arcs."""

ARC_SHADER = '''
struct VertexInput {
    @location(0) quad_pos: vec2f,      // Basic quad vertex position
    @location(1) start: vec2f,         // Start point of segment
    @location(2) end: vec2f,           // End point of segment
    @location(3) start_dir: vec2f,     // Direction at start
    @location(4) end_dir: vec2f,       // Direction at end
    @location(5) color: vec4f,         // Segment color
    @location(6) width: f32,           // Line width
};

struct ViewUniform {
    world_center: vec2f,
    world_size: vec2f,
};

@group(0) @binding(0) var<uniform> view: ViewUniform;

struct VertexOutput {
    @builtin(position) position: vec4f,
    @location(0) color: vec4f,
    @location(1) quad_pos: vec2f,      // Pass quad position to fragment shader
};

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
    var out: VertexOutput;
    
    // Interpolate position along segment based on quad x coordinate
    let t = in.quad_pos.x + 0.5;  // Convert from [-0.5, 0.5] to [0, 1]
    let dir = mix(in.start_dir, in.end_dir, t);
    let pos = mix(in.start, in.end, t);
    
    // Calculate offset based on quad y coordinate and width
    let normal = vec2f(-dir.y, dir.x);  // Perpendicular to direction
    let offset = normal * in.width * in.quad_pos.y;
    
    // Calculate final world position
    let world_pos = pos + offset;
    
    // Transform to screen space
    let screen_pos = (world_pos - view.world_center) / (view.world_size * 0.5);
    out.position = vec4f(screen_pos, 0.0, 1.0);
    out.color = in.color;
    out.quad_pos = in.quad_pos;  // Pass through for antialiasing
    
    return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4f {
    // Calculate distance from center line (y=0)
    let dist = abs(in.quad_pos.y);
    
    // Create smooth falloff at edges
    let alpha = 1.0 - smoothstep(0.8, 1.0, dist);
    
    // Apply alpha to color
    var color = in.color;
    color.a *= alpha;
    return color;
}
''' 