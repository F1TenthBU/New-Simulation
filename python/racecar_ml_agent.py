from mlagents_envs.environment import UnityEnvironment
from mlagents_envs.side_channel.engine_configuration_channel import EngineConfigurationChannel
from mlagents_envs.base_env import ActionTuple
import numpy as np
import threading
import time

class RacecarMLAgent:
    def __init__(self, env_path, time_scale=1.0):
        self.engine_configuration_channel = EngineConfigurationChannel()
        self.env = UnityEnvironment(file_name=env_path, side_channels=[self.engine_configuration_channel])
        self.engine_configuration_channel.set_configuration_parameters(time_scale=time_scale)
        self.env.reset()
        self.behavior_name = list(self.env.behavior_specs.keys())[0]
        self.linear_acceleration = []
        self.angular_velocity = []
        self.lidar_data = []
        self.speed = 0.0
        self.angle = 0.0
        self.running = False
        self.thread = None

    def _run(self):
        while self.running:
            decision_steps, terminal_steps = self.env.get_steps(self.behavior_name)
            
            self.linear_acceleration = decision_steps[agent_id].obs[0][:3]
            self.angular_velocity = decision_steps[agent_id].obs[0][3:6]

            # extract the data from the environment and set the action
            for agent_id in decision_steps:
                # Read data from observations
                self.lidar_data = decision_steps[agent_id].obs[0][6:]
                # print(f"observation len = {len(decision_steps[agent_id].obs[0])}.")

                # Custom action for speed and angle
                action = [self.angle, self.speed]
                action_tuple = ActionTuple(continuous=np.array([action], dtype=np.float32))
                self.env.set_action_for_agent(self.behavior_name, agent_id, action_tuple)
                
            # Step the environment
            self.env.step()
            time.sleep(0.01)  # update at 100 Hz

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()

    def close(self):
        self.stop()
        self.env.close()

    def get_lidar_data(self):
        return self.lidar_data
    
    def get_linear_acceleration(self):
        return self.linear_acceleration
    
    def get_angular_velocity(self):
        return self.angular_velocity

    def set_speed_and_angle(self, speed, angle):
        self.speed = speed
        self.angle = angle