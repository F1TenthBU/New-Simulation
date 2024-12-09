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
4. After you opened it, go to "File"-->"Build and Run" to build the app. Alternatively, you can press "Command + B" for this step. You can use the keyboard to drive the car around the sample track. After that, you can close this app.
5. Now, cd to python directory `cd python`. And now, run racecar_ml_agent_template.py file to make sure your python can communicate with the Unity: `python racecar_ml_agent_template.py`. This should open up the app again, and if the app doesn't crash, you are good to go for your own algorithm.


# How to Train with native ML Agent in Unity:
Use command `mlagents-learn {NNParameter.yaml} --run-id={a unique name for this training session}`

Note: If you have to quit (Ctrl-C) before it finishes training, you can run pass in `--resume` flag to the command. `mlagents-learn {NNParameter.yaml} --run-id={a unique name for this training session} --resume`

When the message "Start training by pressing the Play button in the Unity Editor" is displayed on the screen, you can press the Play button in Unity to start training in the Editor.

## Observe the training:
* `tensorboard --logdir results` then go to `localhost:6006` on your browser.


### Code reference from the MIT simulation:
Initial setup includes codes from MIT simulation:
* Scripts folder: CenterOfMass.cs 
* Scripts/Racecar folder: Racecar.cs, RacecarModule,cs, RacecarNWH.cs, Drive.cs, PhysicsModule.cs, Lidar.cs and CameraModule.cs
* Scripts/Static folder: Constants.cs, NormalDist.cs, Settings.csScripts/UI folder: Hud.cs, ScreenManger.cs

Modification on those files were later adapted.