"""Test script for combined gaussian and arc rendering."""

import numpy as np
from python_racer.renderers.gaussians.renderer import GaussianRenderer, Gaussians
from python_racer.renderers.arcs.renderer import ArcRenderer, Arc
from python_racer.visualization.window_state import WindowState

def main():
    width, height = 1024, 768
    
    window_state = WindowState.create(
        width=width,
        height=height,
        title="Composite Test"
    )
    
    # Create and attach renderers
    gaussian_renderer = GaussianRenderer(window_state.device, window_state.format)
    arc_renderer = ArcRenderer(window_state.device, window_state.format)
    
    window_state.attach_renderer(gaussian_renderer)
    window_state.attach_renderer(arc_renderer)
    
    # Create grid of gaussians
    x, y = np.meshgrid(np.linspace(-10, 10, 21), np.linspace(-10, 10, 21))
    positions = np.stack([x.flatten(), y.flatten()], axis=1).astype(np.float32)
    
    gaussians = Gaussians(
        pos=positions,
        std=np.full(len(positions), 0.1, dtype=np.float32),
        intensity=np.ones(len(positions), dtype=np.float32)
    )
    
    # Rainbow colors for arcs
    colors = [
        [1.0, 0.0, 0.0, 0.8],  # Red
        [1.0, 0.5, 0.0, 0.8],  # Orange
        [1.0, 1.0, 0.0, 0.8],  # Yellow
        [0.0, 1.0, 0.0, 0.8],  # Green
        [0.0, 0.0, 1.0, 0.8],  # Blue
        [0.3, 0.0, 0.5, 0.8],  # Indigo
        [0.5, 0.0, 0.5, 0.8],  # Violet
    ]
    
    t = np.linspace(-5, 5, 100)
    arcs = [
        Arc(
            points=np.column_stack([
                t,
                (i - 3 + np.sin(t * (1.0 + i * 0.2)) * (0.5 + i * 0.3))
            ]).astype(np.float32),
            color=np.array(color, dtype=np.float32),
            width=0.1 + i * 0.05
        )
        for i, color in enumerate(colors)
    ]
    
    gaussian_renderer.update(gaussians)
    arc_renderer.update(arcs)
    
    window_state.game_loop()

if __name__ == "__main__":
    main() 