########################################################################################
# Imports
########################################################################################
# Example usage of RacecarMLAgent class:
from racecar_ml_agent import RacecarMLAgent
import sys, time, os
import numpy as np
import matplotlib.pyplot as plt
import math
from nptyping import NDArray
from typing import Any, Tuple

current_directory = os.path.dirname(os.path.abspath(__file__))
print("Current directory path:", current_directory)
env_path = os.path.join(current_directory, "../Mac.app")
rc = RacecarMLAgent(env_path, time_scale=1.0)


########################################################################################
# Global variables
########################################################################################
rc = RacecarMLAgent(env_path, worker_id=1, time_scale=1.0)

# Declare any global variables here
global speed, angle, speed_offset, angle_offset, accumulated_time

speed = 1.0
angle = 0.0
speed_offset = 0.5
angle_offset = 1.0

accumulated_time = 0  # To accumulate elapsed time

# Lidar parameters
LIDAR_FREQUENCY = 6  # 6 Hz (6 updates per second), according to current sim
UPDATE_INTERVAL = 1.0 / LIDAR_FREQUENCY  # ~0.167 seconds per update

########################################################################################
# GaussianMap Class
########################################################################################
class GaussianMap:
    def __init__(self, x_res=300, y_res=300, sigma=10, decay_rate=0.99):
        self.x_res = x_res
        self.y_res = y_res
        self.sigma = sigma
        self.decay_rate = decay_rate
        self.gaussian_map = np.zeros((x_res, y_res))
        self.x_center = x_res // 2
        self.y_center = y_res // 2
    
    # Vectorized function
    def apply_gaussian(self, distance, angle):
        if distance == 0:
            return

        y = int(self.y_center - distance * np.cos(angle))  # Adjust y-axis
        x = int(self.x_center + distance * np.sin(angle))  # Adjust x-axis

        if 0 <= x < self.x_res and 0 <= y < self.y_res:
            xv, yv = np.meshgrid(np.arange(self.x_res), np.arange(self.y_res))
            gaussian = np.exp(-((xv - x) ** 2 + (yv - y) ** 2) / (2 * self.sigma ** 2))
            self.gaussian_map += gaussian  # Accumulate Gaussian data
    
    def update_gaussian_map(self, lidar_samples):
        # Modify #1: 
        # Reset the Gaussian map with zeros array
        self.gaussian_map = np.zeros((self.x_res, self.y_res))

        num_samples = len(lidar_samples)
        angles = np.linspace(0, 2 * np.pi, num_samples)

        # Create a Gaussian template within a limited radius
        radius = int(3 * self.sigma)
        xv, yv = np.meshgrid(np.arange(-radius, radius + 1), np.arange(-radius, radius + 1))
        gaussian_template = np.exp(-(xv ** 2 + yv ** 2) / (2 * self.sigma ** 2))

        # Apply the Gaussian template at each lidar sample point
        for i, distance in enumerate(lidar_samples):
            if distance == 0:
                continue

            angle = angles[i]
            y = int(self.y_center - distance * np.cos(angle))
            x = int(self.x_center + distance * np.sin(angle))

            # Check if the point is within bounds
            if 0 <= x < self.x_res and 0 <= y < self.y_res:
                # Define the range in the gaussian_map to update
                x_start = max(0, x - radius)
                x_end = min(self.x_res, x + radius + 1)
                y_start = max(0, y - radius)
                y_end = min(self.y_res, y + radius + 1)

                # Define the corresponding range in the gaussian_template
                template_x_start = max(0, radius - x)
                template_y_start = max(0, radius - y)
                template_x_end = template_x_start + (x_end - x_start)
                template_y_end = template_y_start + (y_end - y_start)

                # Accumulate Gaussian data within the bounds
                self.gaussian_map[y_start:y_end, x_start:x_end] += gaussian_template[template_y_start:template_y_end, template_x_start:template_x_end]


        # # Modify #2: apply vectorize
        # # Reset the Gaussian map with zeros array
        # self.gaussian_map = np.zeros((self.x_res, self.y_res))

        # num_samples = len(lidar_samples)
        # angles = np.linspace(0, 2 * np.pi, num_samples)

        # # Vectorize the function
        # vectorized_apply_gaussian = np.vectorize(self.apply_gaussian)

        # # Apply the vectorized function to all lidar samples and angles
        # vectorized_apply_gaussian(lidar_samples, angles)

        # temp_gau = self.gaussian_map.copy()

        # # Original code
        # # Reset the Gaussian map with JAX zeros array
        # self.gaussian_map = np.zeros((self.x_res, self.y_res))

        # num_samples = len(lidar_samples)
        # angles = np.linspace(0, 2 * np.pi, num_samples)

        # for i, distance in enumerate(lidar_samples):
        #     if distance == 0:
        #         continue

        #     angle = angles[i]
        #     y = int(self.y_center - distance * np.cos(angle))  # Adjust y-axis
        #     x = int(self.x_center + distance * np.sin(angle))  # Adjust x-axis
        #     if 0 <= x < self.x_res and 0 <= y < self.y_res:
        #         xv, yv = np.meshgrid(np.arange(self.x_res), np.arange(self.y_res))
        #         gaussian = np.exp(-((xv - x) ** 2 + (yv - y) ** 2) / (2 * self.sigma ** 2))
        #         self.gaussian_map += gaussian  # Accumulate Gaussian data
        
        # difference = np.abs(temp_gau - self.gaussian_map)
        # # print(f"Maximum difference: {np.max(difference)}")
        # print(f"Average difference: {np.average(difference)}")

    def visualize_gaussian_map(self, optimal_angle, radius):
        plt.clf()  # Clear the previous figure
        plt.imshow(self.gaussian_map, cmap='hot', interpolation='nearest')
        plt.colorbar(label='Intensity')
        plt.title('Gaussian Map with Decay')

        angle_rad = np.radians(optimal_angle-90)
        x_end = self.x_center + radius * np.cos(angle_rad)
        y_end = self.y_center + radius * np.sin(angle_rad)
        plt.plot(x_end, y_end, 'x', color='magenta', markersize=10, label='Optimal Direction')

        # angle_rad_detect = np.radians(optimal_angle-90)
        # x_end_detect = self.x_center + radius* (current_detect_pt/70) * np.cos(angle_rad_detect)
        # y_end_detect = self.y_center + radius * np.sin(angle_rad_detect)
        # plt.plot(x_end_detect, y_end_detect, 'x', color='yellow', markersize=10, label='Left Bound')

        angle_rad_left = np.radians(-180)
        x_end_left = self.x_center + radius * np.cos(angle_rad_left)
        y_end_left = self.y_center + radius * np.sin(angle_rad_left)
        plt.plot(x_end_left, y_end_left, 'x', color='blue', markersize=10, label='Left Bound')

        angle_rad_right = np.radians(0)
        x_end_right = self.x_center + radius * np.cos(angle_rad_right)
        y_end_right = self.y_center + radius * np.sin(angle_rad_right)
        plt.plot(x_end_right, y_end_right, 'x', color='yellow', markersize=10, label='Left Bound')



        plt.pause(0.001)  # Small pause to update the figure without blocking

########################################################################################
# PathPlanner Class
########################################################################################
class PathPlanner:
    def __init__(self, gaussian_map, x_center, y_center):
        self.gaussian_map = gaussian_map  # 2D Gaussian heatmap
        self.x_center = x_center
        self.y_center = y_center

    def find_optimal_direction(self, radius, gamma=0.99):
        """
        Find the optimal direction to go based on the Gaussian map within a half-circle.
        Parameters:
            x_center, y_center: Center position of the car.
            radius: Radius of the half-circle in front of the car.
        Returns:
            optimal_direction: Angle (in degrees) of the optimal direction to go.
        """
        gaussian_map = self.gaussian_map.gaussian_map  # Assuming a 2D array of Gaussian values
        optimal_values = []  # To store summed Gaussian values for each angle

        """ Original code begin
        """
        # Iterate over the 180-degree half-circle in front (360 points for finer resolution)
        for angle_deg in np.linspace(-180, 0, 360):  # -180 to 0 degrees relative to the car's heading
            angle_rad = np.radians(angle_deg)
            
            # Calculate the end point of the line on the circle
            x_end = self.x_center + radius * np.cos(angle_rad)
            y_end = self.y_center + radius * np.sin(angle_rad)
            
            # Sample 50 points from the end point to the center
            x_samples = np.linspace(self.x_center, x_end, 50)
            y_samples = np.linspace(self.y_center, y_end, 50)
            
            # Get the Gaussian values at each sampled point
            gaussian_values = []
            # for x, y in zip(x_samples, y_samples):
            for idx, (x, y) in enumerate(zip(x_samples, y_samples), start=1):
                # Ensure the points are within bounds of the gaussian_map
                if 0 <= int(x) < gaussian_map.shape[1] and 0 <= int(y) < gaussian_map.shape[0]:
                    gaussian_values.append(gaussian_map[int(y), int(x)] * (gamma ** idx))
                    # gaussian_values.append(gaussian_map[int(y), int(x)])
            
            # Sum the Gaussian values for this direction
            total_value = np.argmax(gaussian_values)
            optimal_values.append(total_value)

            print("total_value: ", total_value)
            print("optimal_values: ", optimal_values[:10])

        # Find the direction with the minimum Gaussian value
        optimal_index = np.argmin(optimal_values)
        optimal_direction = np.linspace(-90, 90, 360)[optimal_index]
        print("angle now: ", optimal_direction)
        """ Original code end
        """

        """ Vectorized code begin
        """
        # # Define the angles for the 180-degree half-circle
        # angle_deg = np.linspace(-180, 0, 360)
        # angle_rad = np.radians(angle_deg)

        # # Calculate the end points (x_end, y_end) for each angle in vectorized form
        # x_end = self.x_center + radius * np.cos(angle_rad)
        # y_end = self.y_center + radius * np.sin(angle_rad)

        # # Generate 50 points along the line from (x_end, y_end) to the car's center in vectorized form
        # num_samples = 100
        # x_samples = np.linspace(self.x_center, x_end[:, np.newaxis], num_samples)
        # y_samples = np.linspace(self.y_center, y_end[:, np.newaxis], num_samples)
        
        # # Ensure the samples are within the Gaussian map bounds
        # x_indices = np.clip(x_samples.astype(int), 0, gaussian_map.shape[1] - 1)
        # y_indices = np.clip(y_samples.astype(int), 0, gaussian_map.shape[0] - 1)

        # # Get the Gaussian values at each sampled point and apply the gamma weighting
        # idx_array = np.arange(1, num_samples + 1)  # Array for the exponent index
        # gamma_weights = gamma ** idx_array  # Apply gamma weighting
        # weighted_values = gaussian_map[y_indices, x_indices] * gamma_weights

        # # Get the maximum weighted Gaussian values along each line to get the total value per angle
        # total_values = np.max(weighted_values, axis=1)
        # # current_detect_pt = np.argmax(weighted_values, axis=1)
        # # print("current_detect_pt: ", current_detect_pt[0])
        # print("total_values: ", total_values[:10])

        # # Find the angle with the minimum total Gaussian value
        # optimal_index = np.argmin(total_values)
        # # current_detect_pt_idx = current_detect_pt[optimal_index]
        # # print("current_detect_pt_idx: ", current_detect_pt_idx)
        # optimal_direction = angle_deg[optimal_index] + 180
        # print("angel before 180: ", optimal_direction -180)
        # print("angel now: ", optimal_direction)

        """ Vectorized code end
        """
        
        return optimal_direction


########################################################################################
# Functions for update lidar and controlling the car
########################################################################################
def control_car(optimal_angle, speed):
    """
    Control the car based on the optimal direction calculated from LiDAR data.
    """
    # Calculate the steering angle based on the optimal direction
    # Assuming `optimal_angle` is the angle in radians to turn towards
    # Normalize the angle to fit within -1.0 (left) and 1.0 (right) for the steering
    # optimal_angle_rad = np.radians(optimal_angle)
    max_turn_angle = np.pi / 4  # 45 degrees, adjust as needed
    steering_angle = np.clip(optimal_angle / max_turn_angle, -1.0, 1.0)

    # Send the control command to the car
    rc.set_speed_and_angle(speed, steering_angle)

def update_lidar_and_visualize():
    try:
        lidar_samples = rc.lidar.get_samples()  # Fetch new lidar data
        # print("lidar sample: ", lidar_samples[:6])

        if lidar_samples is not None:
            start = time.time()
            gaussian_map.update_gaussian_map(lidar_samples)  # Update heatmap
            # print(time.time() - start)
            # Calculate the optimal path
            path_planner = PathPlanner(gaussian_map, gaussian_map.x_center, gaussian_map.y_center)
            radius = 50
            optimal_angle = path_planner.find_optimal_direction(radius)
            control_car(optimal_angle, 0.5)
            # control_car(0, 1)
            print(time.time() - start)
            print("angle: ", optimal_angle)

        gaussian_map.visualize_gaussian_map(optimal_angle, radius)  # Display the heatmap

    except ValueError as e:
        print(f"Error fetching LiDAR samples: {e}. Skipping this update.")


########################################################################################
# Functions for racecar: start(), update()
########################################################################################

# [FUNCTION] The start function is run once every time the start button is pressed
def start():
    global speed, angle, speed_offset, angle_offset, accumulated_time

    speed = 1.0  # The initial speed is at 1.0
    angle = 0.0  # The initial turning angle away from the center is at 0.0
    speed_offset = 0.5  # The initial speed offset is 0.5
    angle_offset = 1.0  # The initial angle offset is 1.0

    accumulated_time = 0.0  # Reset accumulated time on start

    # This tells the car to begin at a standstill
    rc.stop()

# [FUNCTION] After start() is run, this function is run once every frame, 60fps
def update():
    global speed, angle, speed_offset, angle_offset, accumulated_time

    # Update the accumulated time with the delta time from each frame
    # accumulated_time += rc.get_delta_time()
    # print("time: ", accumulated_time)
    
    # Control the RACECAR using the controller
    # if rc.controller.get_trigger(rc.controller.Trigger.RIGHT) > 0.5:
    #     speed = speed_offset
    # elif rc.controller.get_trigger(rc.controller.Trigger.LEFT) > 0.5:
    #     speed = -speed_offset
    # else:
    #     speed = 0
      
    # (x, y) = rc.controller.get_joystick(rc.controller.Joystick.LEFT)
    # if x > 0.5:
    #     angle = angle_offset
    # elif x < -0.5:
    #     angle = -angle_offset
    # else:
    #     angle = 0

    # if rc.controller.was_pressed(rc.controller.Button.A):
    #     speed_offset += 0.1
    #     speed_offset = min(speed_offset, 1.0)
    #     print(f"Speed Increased! Current Speed Offset: {speed_offset}")
    
    # if rc.controller.was_pressed(rc.controller.Button.B):
    #     speed_offset -= 0.1
    #     speed_offset = max(speed_offset, 0.0)
    #     print(f"Speed Decreased! Current Speed Offset: {speed_offset}")

    # if rc.controller.was_pressed(rc.controller.Button.X):
    #     angle_offset += 0.1
    #     angle_offset = min(angle_offset, 1.0)
    #     print(f"Angle Increased! Current Angle Offset: {angle_offset}")
    
    # if rc.controller.was_pressed(rc.controller.Button.Y):
    #     angle_offset -= 0.1
    #     angle_offset = max(angle_offset, 0.0)
    #     print(f"Angle Decreased! Current Angle Offset: {angle_offset}")

    # Send the speed and angle values to the RACECAR
    # rc.drive.set_speed_angle(speed, angle)

    # if accumulated_time >= UPDATE_INTERVAL:
    if True:
        # print("time",  accumulated_time)
        update_lidar_and_visualize()
        accumulated_time = 0
    


#set a maximum and make the std larger. Keep the last 360 gaussians in a buffer. Delete the rest.
########################################################################################
# DO NOT MODIFY: Register start and update and begin execution
########################################################################################

if __name__ == "__main__":
    gaussian_map = GaussianMap(sigma=35, decay_rate=0.98) 
    try:
        rc.start()

        while True:
            update()
            # Sleep for a short duration to simulate real-time control
            # racecar.set_speed_and_angle(speed, angle)
            time.sleep(0.1)

    except KeyboardInterrupt:
        # Close the environment when the script is interrupted
        rc.close()