"""Test script for arc rendering capabilities."""

import numpy as np
from python_racer.renderers.arcs.renderer import ArcRenderer, Arc
from python_racer.visualization.window_state import WindowState

def hsv_to_rgb(h: np.ndarray) -> np.ndarray:
    """Vectorized HSV to RGB conversion."""
    h = h * 6.0
    h_i = h.astype(int) % 6
    f = h - h_i
    
    # Create arrays for all hues
    t = f.reshape(-1, 1)
    q = (1.0 - f).reshape(-1, 1)
    n = np.zeros_like(t)
    o = np.ones_like(t)
    
    # Create RGB patterns for each sector
    patterns = np.array([
        [o, t, n],  # Red to Yellow
        [q, o, n],  # Yellow to Green
        [n, o, t],  # Green to Cyan
        [n, q, o],  # Cyan to Blue
        [t, n, o],  # Blue to Magenta
        [o, n, q],  # Magenta to Red
    ])
    
    # Select correct pattern for each hue
    rgb = np.zeros((len(h), 3))
    for i in range(6):
        mask = (h_i == i)
        if np.any(mask):
            rgb[mask] = np.column_stack([
                patterns[i, 0][mask],
                patterns[i, 1][mask],
                patterns[i, 2][mask]
            ])
    
    # Add alpha channel
    alpha = np.full((len(h), 1), 0.5)
    return np.hstack([rgb, alpha]).astype(np.float32)

def main():
    """Run the arc renderer test."""
    width, height = 1024, 768
    
    # Create window state
    window_state = WindowState.create(
        width=width,
        height=height,
        title="Arc Test (1000 curves)"
    )
    
    # Create and attach renderer
    renderer = ArcRenderer(window_state.device, window_state.format)
    window_state.attach_renderer(renderer)

    # Create 1000 test arcs with different parameters
    num_arcs = 1000
    
    # Generate colors using vectorized HSV to RGB conversion
    hues = np.linspace(0, 1, num_arcs)
    colors = hsv_to_rgb(hues)
    
    # Generate curve parameters
    t = np.linspace(-5, 5, 100)
    t_mesh = np.tile(t, (num_arcs, 1))
    
    # Generate varying parameters for all curves at once
    indices = np.arange(num_arcs)
    freqs = 0.5 + (indices % 5) * 0.2
    amps = 0.2 + (indices % 3) * 0.1
    phases = (indices / num_arcs) * 2 * np.pi
    y_offsets = -5 + (indices / num_arcs) * 10
    widths = 0.02 + (indices % 5) * 0.01
    
    # Calculate all y values at once
    y_values = (y_offsets[:, np.newaxis] + 
               np.sin(t_mesh * freqs[:, np.newaxis] + phases[:, np.newaxis]) * 
               amps[:, np.newaxis])
    
    # Create x coordinates for all curves
    x_values = np.tile(t, (num_arcs, 1))
    
    # Create all points arrays at once
    points = np.stack([x_values, y_values], axis=2).astype(np.float32)
    
    # Create all arcs
    arcs = [
        Arc(points=points[i], color=colors[i], width=widths[i])
        for i in range(num_arcs)
    ]
    
    # Update renderer with arcs
    renderer.update(arcs)
    
    # Run the window
    window_state.game_loop()

if __name__ == "__main__":
    main() 