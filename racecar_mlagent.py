from mlagents_envs.environment import UnityEnvironment
from mlagents_envs.side_channel.engine_configuration_channel import EngineConfigurationChannel
from mlagents_envs.base_env import ActionTuple
import numpy as np

# Set up the engine configuration
engine_configuration_channel = EngineConfigurationChannel()

# Load the Unity environment with the side channel
env = UnityEnvironment(file_name="/Users/ruihang/Dev/BU F1Tenth/Simulation/Mac.app", side_channels=[engine_configuration_channel])

# Set the engine configuration parameters (1 means real time.)
engine_configuration_channel.set_configuration_parameters(time_scale=1)

# Interact with the environment
env.reset()
behavior_name = list(env.behavior_specs.keys())[0]

while True:
    decision_steps, terminal_steps = env.get_steps(behavior_name)

    # Example of custom logic for agent actions (only 1 agent as of now)
    for agent_id in decision_steps:
        # Read data from observations
        speed = decision_steps[agent_id].obs[0][:3]
        angle = decision_steps[agent_id].obs[0][3:6]
        lidar_data = decision_steps[agent_id].obs[0][6:]  # Assuming Lidar data starts from the 3rd observation
        # print(f"observation len = {len(decision_steps[agent_id].obs[0])}.")

        # Custom action for speed and angle
        action = [0.5, 1]  # angle, speed
        action_tuple = ActionTuple(continuous=np.array([action], dtype=np.float32))
        env.set_action_for_agent(behavior_name, agent_id, action_tuple)
        
    # Step the environment
    env.step()