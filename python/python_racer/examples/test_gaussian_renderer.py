"""Test script for gaussian point cloud rendering."""

import numpy as np
from python_racer.renderers.gaussians.renderer import GaussianRenderer
from python_racer.visualization.window_state import WindowState
from python_racer.types.geometry import create_random_gaussians

def main():
    """Run the gaussian renderer test."""
    width, height = 1024, 768
    
    # Create window state
    window_state = WindowState.create(
        width=width,
        height=height,
        title="Gaussian Test"
    )
    
    # Create and attach renderer
    renderer = GaussianRenderer(window_state.device, window_state.format)
    window_state.attach_renderer(renderer)
    
    # Create a million random gaussians
    gaussians = create_random_gaussians(n_points=1_000_000, spread=5000.0)
    
    # Update renderer with gaussians
    renderer.update(gaussians)
    
    # Run the window
    window_state.game_loop()

if __name__ == "__main__":
    main() 