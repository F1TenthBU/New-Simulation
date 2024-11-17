from python_racer.agent.racecar_ml_agent import RacecarMLAgent
from python_racer.gaussians.game_engine import GameEngine, WindowConfig
from python_racer.gaussians.gaussian_game import GameState, Arc
from wgpu.gui.auto import run
import glfw
import multiprocessing as mp
from multiprocessing import Process, Queue
import numpy as np
import time

def predict_car_arc(pos: np.ndarray, heading: float, speed: float, wheel_angle: float, 
                    linear_accel: np.ndarray, angular_vel: np.ndarray,
                    num_points: int = 20, prediction_time: float = 1.0, debug: bool = False) -> np.ndarray:
    """Predict car's path based on current state."""
    # Scale factors to match LIDAR scale
    SPEED_SCALE = 10.0  # Scale to match visible range
    MIN_SPEED = 0.1  # Lower threshold to see more movement
    
    # Use forward acceleration (Z-axis) as speed indicator
    forward_speed = linear_accel[2]  # Unity Z-axis = forward
    turn_rate = -angular_vel[1]  # Flip sign to match LIDAR space rotation
    
    if debug:
        print(f"Forward speed: {forward_speed:.2f}, Turn rate: {turn_rate:.2f}")
        print(f"Raw physics: accel={linear_accel}, ang_vel={angular_vel}")

    if forward_speed < MIN_SPEED:
        # If nearly stopped, just show a short line forward
        y = np.linspace(0, SPEED_SCALE * 0.2, num_points)
        x = np.zeros_like(y)
        return np.column_stack([x, y]).astype(np.float32)

    # Calculate time steps
    times = np.linspace(0, prediction_time, num_points)
    
    # Start at origin pointing up (+y)
    x = np.zeros_like(times)
    y = np.zeros_like(times)
    
    # For each time step, calculate position based on current motion
    angle = 0  # Start pointing up
    for i in range(1, len(times)):
        dt = times[i] - times[i-1]
        # Update angle based on turn rate
        angle += turn_rate * dt
        # Move forward in current direction
        dx = forward_speed * np.sin(angle) * dt
        dy = forward_speed * np.cos(angle) * dt
        # Update position
        x[i] = x[i-1] + dx
        y[i] = y[i-1] + dy
    
    # Scale the path
    x *= SPEED_SCALE
    y *= SPEED_SCALE
    
    points = np.column_stack([x, y]).astype(np.float32)
    if debug:
        print(f"Arc points range: x[{np.min(x):.1f}, {max(x):.1f}], y[{min(y):.1f}, {max(y):.1f}]")
        print(f"Turn direction: {'right' if turn_rate < 0 else 'left'}")
    return points

def sim_process(lidar_queue: mp.Queue, command_queue: mp.Queue):
    """Separate process for simulation and LIDAR data collection."""
    racecar = RacecarMLAgent()
    try:
        racecar.start()
        while True:
            # Check for stop command
            try:
                if command_queue.get_nowait() == "STOP":
                    break
            except:
                pass

            # Get LIDAR and physics data
            samples = racecar.lidar.get_samples()
            if samples is not None:
                linear_accel = racecar.physics.get_linear_acceleration()
                angular_vel = racecar.physics.get_angular_velocity()
                speed = racecar.speed
                angle = racecar.angle
                
                # Send all data as a tuple
                lidar_queue.put((samples, linear_accel, angular_vel, speed, angle))
            
            time.sleep(0.01)  # Small sleep to prevent busy waiting
            
    finally:
        racecar.close()

def main():
    # Initialize queues for inter-process communication
    lidar_queue = mp.Queue(maxsize=1)
    command_queue = mp.Queue()
    
    # Start simulation process
    sim_proc = Process(target=sim_process, args=(lidar_queue, command_queue))
    sim_proc.start()
    
    # Initialize visualization
    config = WindowConfig(width=1024, height=768, title="LIDAR Visualizer")
    engine = GameEngine.create(config)
    vis_state = GameState.create(config.width, config.height, engine.canvas, engine.device)
    
    # FPS tracking
    frame_count = 0
    last_fps_update = time.time()
    current_fps = 0
    fps_update_interval = 0.5
    
    latest_data = None
    
    try:
        def frame():
            nonlocal vis_state, frame_count, last_fps_update, current_fps, latest_data
            
            start_time = time.perf_counter()
            
            # Try to get new data
            try:
                latest_data = lidar_queue.get_nowait()
            except:
                pass
            
            lidar_time = time.perf_counter()
            
            # Update visualization if we have data
            if latest_data is not None:
                samples, linear_accel, angular_vel, speed, angle = latest_data
                
                t0 = time.perf_counter()
                new_state = vis_state.update_lidar(samples)
                t1 = time.perf_counter()
                
                if new_state is not None:
                    # Predict car's path
                    arc_points = predict_car_arc(
                        np.array([0.0, 0.0], dtype=np.float32),
                        0.0,
                        speed,
                        angle,
                        np.array(linear_accel),
                        np.array(angular_vel),
                        prediction_time=1.0,
                        debug=(frame_count % 30 == 0)
                    )
                    t2 = time.perf_counter()
                    
                    # Create arc for visualization
                    arc = Arc(
                        points=arc_points,
                        color=np.array([0.0, 1.0, 0.0, 1.0], dtype=np.float32)
                    )
                    
                    # Update state with arc
                    new_state = new_state.update_arc(arc)
                    t3 = time.perf_counter()
                    
                    if frame_count % 30 == 0:
                        print("\nState update timing:")
                        print(f"LIDAR update: {(t1-t0)*1000:.2f}ms")
                        print(f"Arc prediction: {(t2-t1)*1000:.2f}ms")
                        print(f"State update: {(t3-t2)*1000:.2f}ms")
                    
                    vis_state = new_state
            
            update_time = time.perf_counter()
            
            # Handle events
            new_state = vis_state.handle_event(engine.canvas._window, engine.scroll_offset)
            if new_state is not None:
                vis_state = new_state
            
            events_time = time.perf_counter()
            
            # Reset scroll offset
            engine.reset_scroll()
            
            # Render current state
            vis_state.render(engine.canvas)
            render_time = time.perf_counter()
            
            # Update FPS counter
            frame_count += 1
            current_time = time.time()
            if current_time - last_fps_update >= fps_update_interval:
                current_fps = frame_count / (current_time - last_fps_update)
                frame_count = 0
                last_fps_update = current_time
                glfw.set_window_title(engine.canvas._window, f"LIDAR Visualizer - FPS: {current_fps:.1f}")
            
            if frame_count % 30 == 0:
                print("\nFrame timing:")
                print(f"LIDAR update: {(lidar_time - start_time)*1000:.2f}ms")
                print(f"State update: {(update_time - lidar_time)*1000:.2f}ms")
                print(f"Event handling: {(events_time - update_time)*1000:.2f}ms")
                print(f"Rendering: {(render_time - events_time)*1000:.2f}ms")
                print(f"Total frame: {(render_time - start_time)*1000:.2f}ms")
            
            # Request next frame
            engine.canvas.request_draw(frame)
        
        # Start render loop
        engine.canvas.request_draw(frame)
        run()
        
    except KeyboardInterrupt:
        # Clean shutdown
        command_queue.put("STOP")
        sim_proc.join()

if __name__ == "__main__":
    main() 