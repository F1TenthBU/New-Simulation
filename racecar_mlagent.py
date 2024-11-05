from mlagents_envs.environment import UnityEnvironment
from mlagents_envs.side_channel.engine_configuration_channel import EngineConfigurationChannel

# Set up the engine configuration
engine_configuration_channel = EngineConfigurationChannel()

# Load the Unity environment with the side channel
env = UnityEnvironment(file_name="/Users/ruihang/Dev/BU F1Tenth/Simulation/Mac.app", side_channels=[engine_configuration_channel])

# Set the engine configuration parameters
engine_configuration_channel.set_configuration_parameters(time_scale=20.0)

# Interact with the environment
env.reset()
behavior_name = list(env.behavior_specs.keys())[0]
decision_steps, terminal_steps = env.get_steps(behavior_name)

# Example of custom logic for agent actions
for agent_id in decision_steps:
    action = [0.0, 1.0]  # Custom action
    env.set_action_for_agent(behavior_name, agent_id, action)

env.step()