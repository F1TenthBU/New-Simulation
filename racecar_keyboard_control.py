# Example usage of RacecarMLAgent class:
import time
from racecar_ml_agent import RacecarMLAgent
import os
from pynput import keyboard

current_directory = os.path.dirname(os.path.abspath(__file__))
print("Current directory path: ", current_directory)

env_path = current_directory + "/Mac.app"
racecar_agent = RacecarMLAgent(env_path, time_scale=1.0)

# Initialize speed and angle
speed = 0
angle = 0

def on_press(key):
    global speed, angle
    try:
        if key.char == 'w':
            speed = 1.0
        elif key.char == 's':
            speed = -1.0
        elif key.char == 'a':
            angle = -1.0
        elif key.char == 'd':
            angle = 1.0
    except AttributeError:
        pass

def on_release(key):
    global speed, angle
    try:
        if key.char in ['w', 's']:
            speed = 0
        elif key.char in ['a', 'd']:
            angle = 0
    except AttributeError:
        pass

def update():
    # Access Lidar data
    lidar_data = racecar_agent.get_lidar_data()
    # print(f"Lidar data: {lidar_data}")

    # Set speed and angle based on keyboard inputs
    racecar_agent.set_speed_and_angle(speed, angle)

## Do not modify the code below
## Unless you want to change the update sleep time or the setup and close logic
if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    try:
        racecar_agent.start()

        while True:
            update()
            # Sleep for a short duration to simulate real-time control
            time.sleep(0.01)  # Reduce sleep time for more responsive control

    except KeyboardInterrupt:
        # Close the environment when the script is interrupted
        racecar_agent.close()
        listener.stop()