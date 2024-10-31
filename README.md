# Simulation

This repo has our brand new simulation, with our own physics and size of the racecar. No autograder, no levelmanagement. No track from MIT. We build our own track to train ML Agent.
This will helps with streamline the ML learning process.

# Getting ready:
0. Clone this repository and cd to that directory.
1. Create conda envrionment on that folder to keep the python side consistant: `conda env create -f environment.yml && conda activate mlagents`
    
    Note: when you start training, use `conda activate mlagents` to activate the envrionment.
2. Open the repository in Unity. Select the Unity version as suggested. This ensures that the version control won't get messed up.


### Code reference from the MIT simulation:
* Lidar object and Lidar script (Lidar.cs)
* Basic Racecar script and its associated CameraModule class and Controller class (tho we don't need the latter)