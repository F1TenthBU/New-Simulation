# Example usage of RacecarMLAgent class:
import time
from python_racer.agent.racecar_ml_agent import RacecarMLAgent
import os
import numpy as np
import matplotlib.pyplot as plt
import math

racecar = RacecarMLAgent()

speed = 0
angle = 0


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
        x = int(self.x_center - distance * np.sin(angle))  # Adjust x-axis

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
            x = int(self.x_center - distance * np.sin(angle))

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


    def visualize_gaussian_map(self, optimal_angle, radius):
        plt.clf()  # Clear the previous figure
        plt.imshow(self.gaussian_map, cmap='hot', interpolation='nearest')
        plt.colorbar(label='Intensity')
        plt.title('Gaussian Map with Decay')

        angle_rad = np.radians(optimal_angle)
        x_end = self.x_center + radius * np.cos(angle_rad)
        y_end = self.y_center + radius * np.sin(angle_rad)
        plt.plot(x_end, y_end, 'x', color='magenta', markersize=10, label='Optimal Direction')


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
        Find the optimal direction to go based on the Gaussian map within a half-ciracecarle.
        Parameters:
            x_center, y_center: Center position of the car.
            radius: Radius of the half-ciracecarle in front of the car.
        Returns:
            optimal_direction: Angle (in degrees) of the optimal direction to go.
        """
        gaussian_map = self.gaussian_map.gaussian_map  # Assuming a 2D array of Gaussian values
        optimal_values = []  # To store summed Gaussian values for each angle

        """ Original code begin
        """
        # Iterate over the 180-degree half-ciracecarle in front (360 points for finer resolution)
        for angle_deg in np.linspace(-180, 0, 360):  # -180 to 0 degrees relative to the car's heading
            angle_rad = np.radians(angle_deg)
            # print("angle_rad: ", angle_rad)
            
            # Calculate the end point of the line on the ciracecarle
            x_end = self.x_center + radius * np.cos(angle_rad)
            # print("x_end: ", x_end)
            y_end = self.y_center + radius * np.sin(angle_rad)
            # print("y_end: ", y_end)
            
            # Sample 50 points from the end point to the center
            x_samples = np.linspace(self.x_center, x_end, 60)
            # print("x_samples: ", x_samples)
            y_samples = np.linspace(self.y_center, y_end, 60)
            # print("y_samples: ", y_samples)
            # Get the Gaussian values at each sampled point
            gaussian_values = []
            # for x, y in zip(x_samples, y_samples):
            for idx, (x, y) in enumerate(zip(x_samples, y_samples), start=1):
                # Ensure the points are within bounds of the gaussian_map
                if 0 <= int(x) < gaussian_map.shape[1] and 0 <= int(y) < gaussian_map.shape[0]:
                    # rather than this i calculate it gaussian_map[int(y), int(x)]
                    gaussian_values.append(gaussian_map[int(y), int(x)] * (gamma ** idx))
                    # print("gaussian values: ", gaussian_values)
                    # gaussian_values.append(gaussian_map[int(y), int(x)])
            
            # Sum the Gaussian values for this direction
            total_value = np.argmax(gaussian_values)
            optimal_values.append(total_value)

            # print("total_value: ", total_value)
            # print("optimal_values: ", optimal_values[:10])

        # Find the direction with the minimum Gaussian value
        optimal_index = np.argmin(optimal_values)
        optimal_direction = np.linspace(-180, 0, 360)[optimal_index]
        # print("optimal direction: ", optimal_direction)
        # print("angle now: ", optimal_direction)
        
        return optimal_direction

def update_lidar_and_visualize():
    try:
        lidar_samples = racecar.lidar.get_samples()  # Fetch new lidar data
        # print("lidar sample: ", lidar_samples[:6])

        if lidar_samples is not None:
            start = time.time()
            gaussian_map.update_gaussian_map(lidar_samples)  # Update heatmap
            # print(time.time() - start)
            # Calculate the optimal path
            path_planner = PathPlanner(gaussian_map, gaussian_map.x_center, gaussian_map.y_center)
            radius = 8
            optimal_angle = path_planner.find_optimal_direction(radius)
            control_car(optimal_angle, 0.5)
            # control_car(0, 1)
            # print("angle: ", optimal_angle)

        gaussian_map.visualize_gaussian_map(optimal_angle, radius)  # Display the heatmap

    except ValueError as e:
        print(f"Error fetching LiDAR samples: {e}. Skipping this update.")
        
########################################################################################
# Functions for update lidar and controlling the car
########################################################################################
def control_car(optimal_angle, speed_local):
    """
    Control the car based on the optimal direction calculated from LiDAR data.
    """
    global speed, angle
    # Calculate the steering angle based on the optimal direction
    # Assuming `optimal_angle` is the angle in radians to turn towards
    # Normalize the angle to fit within -1.0 (left) and 1.0 (right) for the steering
    # optimal_angle_rad = np.radians(optimal_angle + 90)
    # max_turn_angle = 0.610865  # 35 degrees, adjust as needed
    clipped_angle = np.clip(optimal_angle, -125, -55)
    # if (optimal_angle <= 55):
    #     angle = -1
    # elif (optimal_angle >= 125):
    #     angle = 1
    # else:
        # angle = normalize(optimal_angle, old_min, old_max, new_min, new_max)
    angle = normalize(clipped_angle, old_min, old_max, new_min, new_max)
    # normalized_angle = angle_cur / 70
    # steering_angle = np.clip(optimal_angle, -1.0, 1.0)
    # print(angle_cur, steering_angle)
    # Example for normalizing a value
    print(f"Optimal angle: {optimal_angle}, Speed: {speed_local}, Angle: {angle}")

    # Send the control command to the car
    speed = speed_local
    # angle = steering_angle

old_min, old_max = -180, 0
new_min, new_max = -1, 1
def normalize(value, old_min, old_max, new_min, new_max):
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min
    
def update():
    global speed, angle
    # Access Lidar data
    # print(f"Lidar data: {lidar_data}")
    
    update_lidar_and_visualize()

    # Custom logic to control the car based on Lidar data (change your speed and angle logic here)

## Do not modify the code below
## Unless you want to change the update sleep time or the setup and close logic
if __name__ == "__main__":    
    gaussian_map = GaussianMap(sigma=4.5, decay_rate=0.98)   
    
    try:
        racecar.start()

        while True:
            update()
            # Sleep for a short duration to simulate real-time control
            racecar.set_speed_and_angle(speed, angle)
            time.sleep(0.01)

    except KeyboardInterrupt:
        # Close the environment when the script is interrupted
        racecar.close()