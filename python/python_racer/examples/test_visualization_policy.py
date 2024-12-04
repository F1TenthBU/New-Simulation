from python_racer.policies.base_policy import FlattenedPolicy
from python_racer.policies.reactive_policy import ReactivePolicy
from python_racer.types.observations import RacecarObservation
from python_racer.types.actions import RacecarAction
from python_racer.visualization.visualizer import arc_visualizer, lidar_visualizer, Visualizer
from python_racer.visualization.window_process import VisualizationWindow
from python_racer.envs.racecar_env import RacecarEnv

def main():
    env = RacecarEnv()
    structured_policy = ReactivePolicy()
    policy = FlattenedPolicy(structured_policy)
    
    visualizer = Visualizer.compose(
        arc_visualizer(),
        lidar_visualizer()
    )
    window = VisualizationWindow()
    
    try:
        obs, info = env.reset()
        while True:
            structured_obs = RacecarObservation.from_unity_obs(obs)
            action = policy.act(obs)
            viz = visualizer.visualize(structured_obs, RacecarAction.from_numpy(action))
            window.update(viz)
            obs, reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
    
    finally:
        window.close()
        env.close()

if __name__ == "__main__":
    main() 