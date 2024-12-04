from dataclasses import dataclass, field
import numpy as np
from .emitter import EventEmitter
import wgpu

@dataclass(frozen=True)
class WindowResizeEvent:
    size: np.ndarray  # Current [width, height]
    previous_size: np.ndarray  # Previous [width, height]

@dataclass(frozen=True)
class MouseMoveEvent:
    position: np.ndarray  # [x, y] in normalized coordinates

@dataclass(frozen=True)
class MouseDragEvent:
    start: np.ndarray
    current: np.ndarray
    delta: np.ndarray

@dataclass(frozen=True)
class ScrollEvent:
    offset: np.ndarray  # [x, y] scroll offset

@dataclass(frozen=True)
class RenderEvent:
    command_encoder: wgpu.GPUCommandEncoder
    canvas: wgpu.WgpuCanvasInterface
    dt: float

@dataclass(frozen=True)
class WindowEvents:
    window: int  # GLFW window handle
    resize: EventEmitter[WindowResizeEvent] = field(default_factory=EventEmitter)
    mouse_move: EventEmitter[MouseMoveEvent] = field(default_factory=EventEmitter)
    mouse_drag: EventEmitter[MouseDragEvent] = field(default_factory=EventEmitter)
    scroll: EventEmitter[ScrollEvent] = field(default_factory=EventEmitter)
    frame: EventEmitter[float] = field(default_factory=EventEmitter)  # Emits delta time
    render: EventEmitter[RenderEvent] = field(default_factory=EventEmitter)
