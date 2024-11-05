import requests

# Define the base URL of the Unity server
BASE_URL = "http://localhost:5000"

def get_lidar_samples():
    response = requests.get(f"{BASE_URL}/lidar/samples")
    if response.status_code == 200:
        return response.json()  # Assuming the server returns JSON data
    else:
        print("Failed to get lidar samples")
        return None

def set_car_controls(speed, angle):
    data = {
        "speed": speed,
        "angle": angle
    }
    response = requests.post(f"{BASE_URL}/car/control", json=data)
    if response.status_code == 200:
        print("Car controls updated successfully")
    else:
        print("Failed to update car controls")

# Example usage
if __name__ == "__main__":
    # Get lidar samples
    lidar_samples = get_lidar_samples()
    print("Lidar Samples:", lidar_samples)

    # Set car speed and angle
    # set_car_controls(speed=1.0, angle=0.5)