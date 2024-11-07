# Example usage of RacecarMLAgent class:
import time
from racecar_ml_agent import RacecarMLAgent
import os
import pygame

# Initialize pygame
pygame.init()

current_directory = os.path.dirname(os.path.abspath(__file__))
print("Current directory path:", current_directory)

env_path = current_directory + "/Mac.app"
racecar = RacecarMLAgent(env_path, time_scale=1.0)

speed = 0
angle = 0

# Create a pygame window
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Racecar Control")

def update():
    global speed, angle
    # Reset speed and angle
    speed = 0
    angle = 0

    # Access Lidar data
    lidar_data = racecar.get_lidar_data()
    # print(f"Lidar data: {lidar_data}")

    # Handle keyboard events
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        print("W or UP key is pressed")
        speed = 1
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        print("S or DOWN key is pressed")
        speed = -1
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        print("A or LEFT key is pressed")
        angle = -1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        print("D or RIGHT key is pressed")
        angle = 1

## Do not modify the code below
## Unless you want to change the update sleep time or the setup and close logic
if __name__ == "__main__":
    try:
        racecar.start()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise KeyboardInterrupt

            update()
            # Sleep for a short duration to simulate real-time control
            racecar.set_speed_and_angle(speed, angle)
            print(f"Speed: {speed}, Angle: {angle}")
            time.sleep(0.1)

    except KeyboardInterrupt:
        # Close the environment when the script is interrupted
        racecar.close()
        pygame.quit()