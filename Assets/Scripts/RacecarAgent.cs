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
        
        // Add collision state (1.0 for collision, 0.0 for no collision)
        sensor.AddObservation(racecar.Collided ? 1.0f : 0.0f);

        // Add the racecar's Lidar data to the observations
        float[] lidarSamples = racecar.Lidar.Samples;
        for (int i = 0; i < 1081; i++)
        {
            sensor.AddObservation(lidarSamples[i]);
        }
    }

    public override void OnActionReceived(ActionBuffers actions)
    {
        // Apply received actions to the racecar
        racecar.Drive.Angle = actions.ContinuousActions[0];
        racecar.Drive.Speed = actions.ContinuousActions[1];
    }

    public override void Heuristic(in ActionBuffers actionsOut)
    {
        ActionSegment<float> continuousActions = actionsOut.ContinuousActions;
        continuousActions[0] = Input.GetAxis("Horizontal");
        continuousActions[1] = Input.GetAxis("Vertical");
    }
}