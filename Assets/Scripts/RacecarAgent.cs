using System.Collections.Generic;
using Unity.MLAgents;
using Unity.MLAgents.Sensors;
using Unity.MLAgents.Actuators;
using UnityEngine;
using System;

public class RacecarAgent : Agent
{
    public Racecar racecar;

    public override void OnEpisodeBegin()
    {
        // Reset the racecar's position, speed, and angle at the beginning of each episode
        racecar.Drive.Angle = 0;
        racecar.Drive.Speed = 0;

        racecar.transform.localPosition = new Vector3(0, 0, 0);
        racecar.transform.localRotation = Quaternion.Euler(0, 0, 0);

        // Reset the Collided property
        racecar.Collided = false;

        Debug.Log("Starting new episode.");
    }

    public override void CollectObservations(VectorSensor sensor)
    {
        // Add the racecar's velocity to the observations
        sensor.AddObservation(racecar.Physics.LinearVelocity);
        sensor.AddObservation(racecar.Physics.AngularVelocity);

        // Add the racecar's Lidar data to the observations
        float[] lidarSamples = racecar.Lidar.Samples;
        foreach (float sample in lidarSamples)
        {
            sensor.AddObservation(sample);
        }

        // Punish the agent for colliding with obstacles
        if (racecar.Collided)
        {
            Debug.Log("Collision with wall. Starting new episode.");
            EndEpisode();
            SetReward(0);
        }
    }

    public override void OnActionReceived(ActionBuffers actions)
    {
        racecar.Drive.Angle = actions.ContinuousActions[0];
        racecar.Drive.Speed = actions.ContinuousActions[1];

        // Reward the agent for moving forward when lidar data shows no obstacles in front
        if (racecar.Drive.Speed > 0 && racecar.Lidar.IsForwardClear())
        {
            AddReward(racecar.Drive.Speed / 10);
        }

        // Punish the agent for colliding with obstacles
        if (racecar.Collided)
        {
            Debug.Log("Collision with wall. Starting new episode.");
            EndEpisode();
            SetReward(0);
        }
    }

    public override void Heuristic(in ActionBuffers actionsOut)
    {
        ActionSegment<float> continuousActions = actionsOut.ContinuousActions;
        continuousActions[0] = Input.GetAxis("Horizontal");
        continuousActions[1] = Input.GetAxis("Vertical");
    }
}