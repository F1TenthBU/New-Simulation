# Example usage of RacecarMLAgent class:
import time
from python.racecar_ml_agent import RacecarMLAgent
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
print("Current directory path:", current_directory)

env_path = current_directory + "/Mac.app"
racecar = RacecarMLAgent(env_path, time_scale=1.0)

speed = 0
angle = 0

def update():
    global speed, angle
    # Access Lidar data
    lidar_data = racecar.get_lidar_data()
    # print(f"Lidar data: {lidar_data}")

    # Custom logic to control the car based on Lidar data (change your speed and angle logic here)

## Do not modify the code below
## Unless you want to change the update sleep time or the setup and close logic
if __name__ == "__main__":
    try:
        racecar.start()

        while True:
            update()
            # Sleep for a short duration to simulate real-time control
            racecar.set_speed_and_angle(speed, angle)
            time.sleep(0.1)

    except KeyboardInterrupt:
        # Close the environment when the script is interrupted
        racecar.close()