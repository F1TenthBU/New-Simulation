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

env_path = current_directory + "/../Sim.x86_64"
racecar = RacecarMLAgent(env_path, time_scale=1.0)

########################################################################################
# Global variables
########################################################################################

IS_SIM = True
# rc = RacecarMLAgent(env_path, time_scale=1.0)

SHOW_PLOT = False

# >> Constants
WINDOW_SIZE = 8 # Window size to calculate the average distance

# >> Variables
speed = 0.0  # The current speed of the car
angle = 0.0  # The current angle of the car's wheels

# >> !!! TUNING VARIABLES !!!
if IS_SIM:
    PREDICT_LEVEL = 3
    CAR_WIDTH = 30
    UNIT_PATH_LENGTH = 20
    # Initialize PID control variables for angle
    KP = 0.5
    KI = 0.0
    KD = 0.0
else:
    PREDICT_LEVEL = 2
    CAR_WIDTH = 30
    UNIT_PATH_LENGTH = 20
    KP = 0.2
    KI = 0.0
    KD = 0.0

prev_error_angle = 0  # Previous error for angle control
integral_angle = 0  # Integral term for angle control

# Initialize PID control variables for speed
KP_speed = 0.1  # Proportional constant for speed
KI_speed = 0.001  # Integral constant for speed
KD_speed = 0.05  # Derivative constant for speed
prev_error_speed = 0  # Previous error for speed control
integral_speed = 0  # Integral term for speed control

# Initialize desired speed
desired_speed = 0.5  # Set desired speed to 0.5 (you can adjust this value)

flag = 0

########################################################################################
# Functions
########################################################################################

def get_lidar_average_distance(
    scan: NDArray[Any, np.float32], angle: float, window_angle: float = 4
) -> float:
    """
    Finds the average distance of the object at a particular angle relative to the car.

    Args:
        scan: The samples from a LIDAR scan
        angle: The angle (in degrees) at which to measure distance, starting at 0
            directly in front of the car and increasing clockwise.
        window_angle: The number of degrees to consider around angle.

    Returns:
        The average distance of the points at angle in cm.

    Note:
        Ignores any samples with a value of 0.0 (no data).
        Increasing window_angle reduces noise at the cost of reduced accuracy.

    Example::

        scan = rc.lidar.get_samples()

        # Find the distance directly behind the car (6:00 position)
        back_distance = rc_utils.get_lidar_average_distance(scan, 180)

        # Find the distance to the forward and right of the car (1:30 position)
        forward_right_distance = rc_utils.get_lidar_average_distance(scan, 45)
    """
    assert (
        0 <= window_angle < 360
    ), f"window_angle ({window_angle}) must be in the range 0 to 360, and reasonably should not exceed 20."

    # Adjust angle into the 0 to 360 degree range
    angle %= 360

    # Calculate the indices at the edges of the requested window
    center_index: int = int(angle * scan.shape[0] / 360)
    num_side_samples: int = int(window_angle / 2 * scan.shape[0] / 360)
    left_index: int = (center_index - num_side_samples) % len(scan)
    right_index: int = (center_index + num_side_samples) % len(scan)

    # Select samples in the window, handling if we cross the edge of the array
    samples: List[float]
    if right_index < left_index:
        samples = scan[left_index:].tolist() + scan[0 : right_index + 1].tolist()
    else:
        samples = scan[left_index : right_index + 1].tolist()

    # Remove samples with no data (0.0)
    samples = [elem for elem in samples if elem > 0]

    # If no valid samples remain, return 0.0
    if len(samples) == 0:
        return 0.0

    return sum(samples) / len(samples)

def get_farthest_distance_in_range(scan, start, end):
    scan_size = len(scan)
    if start < 0:
        start += scan_size
    if end < 0:
        end += scan_size

    if start <= end:
        values_in_range = scan[start:end + 1]
    else:
        values_in_range = np.concatenate((scan[start:], scan[:end + 1]))

    return np.max(values_in_range)

def lidar_to_2d_coordinates(lidar_data):
    coordinates = []
    for angle in range(360):
        distance = lidar_data[angle]
        # 0 degrees is up (positive y-axis), adjusting angle accordingly
        adjusted_angle_rad = math.radians(90 - angle)  # Shift 0 degrees to point upward
        x = distance * math.cos(adjusted_angle_rad)
        y = distance * math.sin(adjusted_angle_rad)
        coordinates.append((x, y, distance))
    return coordinates

def find_farthest_point(coordinates):
    filtered_points = [point for point in coordinates if point[1] > 0]
    if not filtered_points:
        return None
    farthest_point = max(filtered_points, key=lambda p: p[2])
    return farthest_point

def point_along_line(origin, target, distance):
    vector_x = target[0] - origin[0]
    vector_y = target[1] - origin[1]
    vector_length = math.sqrt(vector_x**2 + vector_y**2)

    if vector_length <= distance * 2:
        return target

    scale = distance / vector_length
    point_x = origin[0] + vector_x * scale
    point_y = origin[1] + vector_y * scale

    return [point_x, point_y]

def find_side_points(coordinates, origin):
    lefts = []
    rights = []
    adding_to_lefts = True

    for i in range(len(coordinates)):
        last_point = coordinates[(i - 1) % len(coordinates)]
        point = coordinates[i]

        if point == origin or (last_point[1] < 0 and point[1] > 0):
            adding_to_lefts = not adding_to_lefts
            continue

        # Skip segments where either coordinate has a negative y-value
        if point[1] <= 0:
            continue

        # Add to lefts or rights based on the current state
        if adding_to_lefts:
            lefts.append(point)
        else:
            rights.append(point)
    
    if len(lefts) == 0 or len(rights) == 0:
        print('WARN! No left or right side.')
        # print(lefts)
        # print(rights)
        return lefts, rights

    return lefts, rights

def find_closest_points_on_sides(origin, midpoint, left_points, right_points):
    y_threshold = origin[1]

    filtered_lefts = [point for point in left_points if not (point[1] > y_threshold)]
    filtered_rights = [point for point in right_points if not (point[1] > y_threshold)]

    closest_left = min(filtered_lefts, key=lambda p: math.hypot(p[0] - midpoint[0], p[1] - midpoint[1]), default=None)
    closest_right = min(filtered_rights, key=lambda p: math.hypot(p[0] - midpoint[0], p[1] - midpoint[1]), default=None)

    # closest_left = min(left_points, key=lambda p: math.hypot(p[0] - midpoint[0], p[1] - midpoint[1]), default=None)
    # closest_right = min(right_points, key=lambda p: math.hypot(p[0] - midpoint[0], p[1] - midpoint[1]), default=None)

    return closest_left, closest_right

def adjust_midpoint(midpoint, closest_left, closest_right, distance=CAR_WIDTH):
    # distance here is different to one in find_adjusted_path_with_points()
    distance_left = math.hypot(midpoint[0] - closest_left[0], midpoint[1] - closest_left[1])
    distance_right = math.hypot(midpoint[0] - closest_right[0], midpoint[1] - closest_right[1])

    if min(distance_left, distance_right) > distance:
        return midpoint

    elif distance_left + distance_right > distance * 2:
        # Find the direction vector along the line connecting closest_left and closest_right
        direction_vector = [closest_right[0] - closest_left[0], closest_right[1] - closest_left[1]]
        line_length = math.hypot(direction_vector[0], direction_vector[1])
        unit_vector = [direction_vector[0] / line_length, direction_vector[1] / line_length] if line_length != 0 else [0, 0]

        # Calculate new position along the line
        if distance_left < distance_right:
            scale = distance - distance_left
            new_x = midpoint[0] + unit_vector[0] * scale
            new_y = midpoint[1] + unit_vector[1] * scale
        else:
            scale = distance - distance_right
            new_x = midpoint[0] - unit_vector[0] * scale
            new_y = midpoint[1] - unit_vector[1] * scale

        return [new_x, new_y]

    else:
        return [(closest_left[0] + closest_right[0]) / 2, (closest_left[1] + closest_right[1]) / 2]

def find_adjusted_path_with_points(origin, target, coordinates, distance=UNIT_PATH_LENGTH):
    current_point = origin
    path_points = [current_point[:2]]  # Store all path points

    lefts, rights = find_side_points(coordinates, origin)

    count = 1
    while True:
        if count % 20 == 0:
            distance *= 2

        next_point = point_along_line(current_point, target, distance)
        # print('next:', next_point)

        if next_point == target:
            path_points.append(target)
            return path_points
        
        closest_left, closest_right = find_closest_points_on_sides(current_point, next_point, lefts, rights)
        # print(closest_left, closest_right)
        if not closest_left or not closest_right:
            adjusted_point = [0,0]
        else:
            adjusted_point = adjust_midpoint(next_point, closest_left, closest_right)

        # print('adjusted_point:', adjusted_point)
        path_points.append(adjusted_point)
        current_point = adjusted_point

        count += 1

def calculate_angle(origin, midpoint):
    vector_x = midpoint[0] - origin[0]
    vector_y = midpoint[1] - origin[1]
    
    angle_rad = math.atan2(vector_x, vector_y)  # atan2 gives angle relative to y-axis (0, 1) with correct sign
    angle_deg = math.degrees(angle_rad)

    return angle_deg

def convert_angle_to_ratio(angle):
    max_angle = 45.0
    ratio = max(min(angle / max_angle, 1.0), -1.0)
    return ratio

def plot_lines_to_farthest_point_in_func(lidar_data, coordinates, farthest_point, path_points):
    plt.clf()  # Clear the previous figure

    coordinates = np.array(coordinates)
    x_coords = coordinates[:, 0]
    y_coords = coordinates[:, 1]

    plt.scatter(x_coords, y_coords, s=10, c='blue', alpha=0.6, label='Lidar Points')
    plt.scatter(*farthest_point, c='red', s=50, label='Farthest Point (y > 0)')

    path_points = np.array(path_points)
    path_x = path_points[:, 0]
    path_y = path_points[:, 1]

    plt.plot(path_x, path_y, 'g-', label='Adjusted Path')

    plt.scatter(path_x, path_y, c='purple', s=30, alpha=0.7, label='Path Points')

    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.grid(True)
    plt.axis('equal')
    plt.legend()

    plt.pause(0.001)

def path_find(lidar_data):
    coordinates = lidar_to_2d_coordinates(lidar_data)
    farthest_point = find_farthest_point(coordinates)
    points = find_adjusted_path_with_points(farthest_point, [0, 0], coordinates)
    # print('PATH: ', points)

    points_distance = PREDICT_LEVEL
    if len(points) < points_distance:
        points_distance = len(points)

    adjusted_midpoint = points[-points_distance]
    angle = calculate_angle([0, 0], adjusted_midpoint)
    ratio = convert_angle_to_ratio(angle)

    print(f"Angle: {angle} degrees")
    print(f"Ratio: {ratio}")

    if SHOW_PLOT:
        plot_lines_to_farthest_point_in_func(lidar_data, coordinates, farthest_point[:-1], points)
    return ratio, farthest_point

def update_lidar():
    """
    Receive the lidar samples and get the average samples from it
    """
    global average_scan

    scan = racecar.get_lidar_data()
    if (len(scan) == 0):
        return False
    
    if (scan[0] == 0.0):
        return False
    
    scan = np.clip(scan, None, 1000)
    
    if not IS_SIM:
        scan_length = len(scan) # 1081, 1 for 0 angle maybe?
        values_per_angle = (scan_length - 1) / 270
        degree_0 = int((scan_length - 1) / 2)
        first_half = scan[:degree_0] # 135 to 0
        backward = np.full(int(90 * values_per_angle - 1), 30)
        second_half = scan[degree_0:] # 0 to -135
        rotated_scan = np.concatenate([second_half, backward, first_half])
    else:
        rotated_scan = scan

    average_scan = np.array([get_lidar_average_distance(rotated_scan, angle, WINDOW_SIZE) for angle in range(360)])
    print(average_scan)
    return

def start():
    """
    This function is run once every time the start button is pressed
    """
    global speed
    global angle

    # Initialize variables
    speed = 0
    angle = 0

    # Set initial driving speed and angle
    # rc.drive.set_speed_angle(speed, angle)
    # Set update_slow to refresh every half second
    #rc.set_update_slow_time(0.5)

    # Print start message
    print(
        ">> Wall Following\n"
        "\n"
        "Controls:\n"
        "    A button = print current speed, angle, and closest values\n"
    )

def update():
    global speed
    global angle
    global prev_error_angle
    global prev_error_speed
    global integral_angle
    global integral_speed
    global average_scan
    global flag

    if update_lidar() == False:
        return
    
    start = time.time()
    angle_error, farthest_point = path_find(average_scan)
    print('time: ', time.time() - start)

    # Update angle integral term
    integral_angle += angle_error

    # Update angle derivative term
    angle_derivative = angle_error - prev_error_angle
    prev_error_angle = angle_error

    # Calculate angle PID output
    angle_pid_output = KP * angle_error + KI * integral_angle + KD * angle_derivative

    # Convert angle PID output to angle
    angle = angle_pid_output

    # # PID control for speed
    # # Calculate speed error (difference between desired and actual speed)
    # speed_error = desired_speed - speed

    # # Update speed integral term
    # integral_speed += speed_error

    # # Update speed derivative term
    # speed_derivative = speed_error - prev_error_speed
    # prev_error_speed = speed_error

    # # Calculate speed PID output
    # speed_pid_output = KP_speed * speed_error + KI_speed * integral_speed + KD_speed * speed_derivative

    # # Convert speed PID output to speed
    # speed += speed_pid_output

    speed = 0.2

    farthest_distance = farthest_point[2]
    if farthest_distance < 350 and flag < 30:
        speed = 0.0
        flag += 1
    elif flag > 0:
        flag += 1
    else:
        flag = 0
    flag %= 60

    # emergency_distance = get_farthest_distance_in_range(average_scan, -45, 45)
    # if emergency_distance < 30:
    #     speed = -1.0

    # Constrain speed and angle within 0.0 to 1.0
    # speed = max(0.0, min(1.0, speed))
    angle = max(-1.0, min(1.0, angle))

    # Set the speed and angle of the car
    racecar.set_speed_and_angle(speed, angle)

    # Print the current speed and angle and closest values when the A button is held down
    # if rc.controller.is_down(rc.controller.Button.A):
    #     print("Speed:", speed, "Angle:", angle)
        # print("Left:", closest_left_angle, ",", closest_left_distance)
        # print("Right:", closest_right_angle, ",", closest_right_distance)
        # print("Front:", closest_front_angle, ",", closest_front_distance)

## Do not modify the code below
## Unless you want to change the update sleep time or the setup and close logic
if __name__ == "__main__":
    try:
        racecar.start()

        while True:
            update()
            # Sleep for a short duration to simulate real-time control
            # racecar.set_speed_and_angle(speed, angle)
            time.sleep(0.1)

    except KeyboardInterrupt:
        # Close the environment when the script is interrupted
        racecar.close()