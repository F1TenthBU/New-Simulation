# Simulation

This repo has our brand new simulation, with our own physics and size of the racecar. No autograder, no levelmanagement. No track from MIT. We build our own track to train ML Agent.
This will helps with streamline the ML learning process.

# Getting ready:
0. Clone this repository and cd to that directory.
1. Create conda envrionment on that folder to keep the python side consistant: `conda env create -f environment.yml && conda activate mlagents`
    
    Note: when you start training, use `conda activate mlagents` to activate the envrionment.

2. For Mac user: in your mlagents envrionment, first do `pip3 install grpcio` and then `python -m pip install mlagents==1.1.0`
    
    You should be able to run `mlagents-learn --help` in the conda envrionment.
3. Open the repository in Unity. Select the Unity version as suggested. This ensures that the version control won't get messed up.


# How to Train:
Use command `mlagents-learn {NNParameter.yaml} --run-id={a unique name for this training session}`

Note: If you have to quit (Ctrl-C) before it finishes training, you can run pass in `--resume` flag to the command. `mlagents-learn {NNParameter.yaml} --run-id={a unique name for this training session} --resume`

When the message "Start training by pressing the Play button in the Unity Editor" is displayed on the screen, you can press the Play button in Unity to start training in the Editor.

## Observe the training:
* `tensorboard --logdir results` then go to `localhost:6006` on your browser.


### Code reference from the MIT simulation:
* Lidar object and Lidar script (Lidar.cs)
* Basic Racecar script and its associated CameraModule class and Controller class (tho we don't need the latter)