﻿using System;
using UnityEngine;

/// <summary>
/// Controls the heads-up display shown to the user during races with a single car.
/// </summary>
public class Hud : ScreenManager
{
    #region Set in Unity Editor
    /// <summary>
    /// The textbox shown when the user fails an objective.
    /// </summary>
    [SerializeField]
    private GameObject FailureMessage;

    /// <summary>
    /// The textbox shown when the user successfully completes a lab.
    /// </summary>
    [SerializeField]
    private GameObject SuccessMessage;
    #endregion

    #region Constants
    /// <summary>
    /// The color used for the background of sensor visualizations.
    /// </summary>
    public static readonly Color SensorBackgroundColor = new Color(0.2f, 0.2f, 0.2f);

    /// <summary>
    /// The number of times the LIDAR map is smaller than the color and depth visualizations.
    /// </summary>
    private const int lidarMapScale = 4;

    /// <summary>
    /// The alpha (transparency) of the Python icon when no script is connected.
    /// </summary>
    private const float unconnectedScriptAlpha = 0.25f;
    #endregion

    #region Public Interface
    #region Overrides
    public override void HandleWin(float time, bool isNewBestTime = false)
    {
        this.SuccessMessage.SetActive(true);
        this.texts[(int)Texts.SuccessMessage].text = isNewBestTime ? "New Best Time!" : "Mission Accomplished!";
        this.texts[(int)Texts.SuccessTime].text = $"Time: {time:F3} seconds";
    }

    public override void HandleFailure(int carIndex, string reason)
    {
        this.FailureMessage.SetActive(true);
        this.texts[(int)Texts.Failure].text = reason;
    }

    public override void UpdateConnectedPrograms(bool[] connectedPrograms)
    {
        this.images[(int)Images.ConnectedProgram].color = connectedPrograms.Length > 0 ? new Color(1, 1, 1, 1) : new Color(1, 1, 1, Hud.unconnectedScriptAlpha);
    }

    public override void UpdateTimeScale(float timeScale)
    {
        this.images[(int)Images.TimeWarp].color = new Color(1, 1, 1, Mathf.Max(0, 1 - Mathf.Sqrt(timeScale)));
        this.texts[(int)Texts.TimeScale].text = timeScale >= 1 ? string.Empty : $"{Mathf.Round(1 / timeScale)}x Slow Motion";
    }

    public override void UpdateTime(float mainTime, float[] keyPointDurations)
    {
        base.UpdateTime(mainTime, keyPointDurations);

        // If the level contains checkpoints, show the time spent on each checkpoint
        if (keyPointDurations.Length > 2)
        {
            string text = $"1) {keyPointDurations[1]:F3}";
            for (int i = 2; i < keyPointDurations.Length; i++)
            {
                if (keyPointDurations[i] == 0)
                {
                    text += $"\n{i}) --";
                }
                else
                {
                    text += $"\n{i}) {keyPointDurations[i]:F3}";
                }
            }

            this.texts[(int)Texts.CheckpointTimes].text = text;
        }
    }
    #endregion

    /// <summary>
    /// The texture containing the depth camera visualization.
    /// </summary>
    public Texture2D DepthVisualization
    {
        get
        {
            return (Texture2D)this.images[(int)Images.DepthFeed].texture;
        }
    }

    /// <summary>
    /// Update the physics statistics shown on the HUD.
    /// </summary>
    /// <param name="speed">The magnitude of the car's linear velocity in m/s.</param>
    /// <param name="linearAcceleration">The car's linear acceleration in m/s^2.</param>
    /// <param name="angularVelocity">The car's angular velocity in rad/s.</param>
    public void UpdatePhysics(float speed, Vector3 linearAcceleration, Vector3 angularVelocity)
    {
        this.texts[(int)Texts.TrueSpeed].text = speed.ToString("F2");
        this.texts[(int)Texts.LinearAcceleration].text = FormatVector3(linearAcceleration);
        this.texts[(int)Texts.AngularVelocity].text = FormatVector3(angularVelocity);
    }
    #endregion

    /// <summary>
    /// The mutable text fields of the HUD, with values corresponding to the index in texts.
    /// </summary>
    private enum Texts
    {
        Message = 0,
        MainTime = 1,
        CheckpointTimes = 2,
        TimeScale = 3,
        TrueSpeed = 8,
        LinearAcceleration = 12,
        AngularVelocity = 15,
        Mode = 17,
        Failure = 19,
        SuccessMessage = 21,
        SuccessTime = 22,
        MaxTime = 28
    }

    /// <summary>
    /// The mutable images of the HUD, with values corresponding to the index in images.
    /// </summary>
    private enum Images
    {
        TimeWarp = 0,
        ColorFeed = 3,
        DepthFeed = 5,
        LidarMap = 7,
        ModeBackground = 9,
        ConnectedProgram = 10,
        ControllerFirstButton = 12
    }

    protected override void Awake()
    {
        base.Awake();

        this.images[(int)Images.LidarMap].texture = new Texture2D(CameraModule.ColorWidth / Hud.lidarMapScale, CameraModule.ColorHeight / Hud.lidarMapScale);
        this.images[(int)Images.DepthFeed].texture = new Texture2D(CameraModule.DepthWidth, CameraModule.DepthHeight);
    }

    private void Start()
    {
        this.FailureMessage.SetActive(false);
        this.SuccessMessage.SetActive(false);

        this.texts[(int)Texts.CheckpointTimes].text = string.Empty;
    }

    protected override void Update()
    {
        base.Update();
    }

    /// <summary>
    /// Formats a vector with a constant as a string with a constant width.
    /// </summary>
    /// <param name="vector">The vector to format.</param>
    /// <returns>The vector formatted as a string with exactly 19 characters.</returns>
    private string FormatVector3(Vector3 vector)
    {
        return $"({FormatFloat(vector.x)},{FormatFloat(vector.y)},{FormatFloat(vector.z)})";       
    }

    /// <summary>
    /// Rounds and formats a float as a string with a constant width.
    /// </summary>
    /// <param name="value">A value less than 10.</param>
    /// <returns>The provided value formatted as a string with exactly five characters.</returns>
    private string FormatFloat(float value)
    {
        string str = value.ToString("F2");

        // Add a leading space if there is no negative sign
        if (str[0] != '-')
        {
            return $" {str}";
        }

        return str;
    }
}
