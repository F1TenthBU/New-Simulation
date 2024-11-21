using System;
using UnityEngine;

/// <summary>
/// Simulates the LIDAR sensor.
/// </summary>
public class Lidar : RacecarModule
{
    #region Constants
    /// <summary>
    /// The number of samples captured in a single rotation.
    /// Based on the Hokuyo Lidar datasheet.
    /// </summary>
    public const int NumSamples = 1440;

    private const int forwardSampleRange = 10; // Number of samples to check in the forward direction
    private const float clearDistanceThreshold = 50.0f; // Distance threshold to consider as clear (in cm)

    /// <summary>
    /// The frequency of the LIDAR motor in hz.
    /// </summary>
    private const int motorFrequency = 40;

    /// <summary>
    /// The number of sample taken per second.
    /// </summary>
    private const int samplesPerSecond = Lidar.NumSamples * Lidar.motorFrequency;

    /// <summary>
    /// The angle at which the LIDAR starts taking samples (in degrees).
    /// Based on the Hokuyo Lidar datasheet.
    /// </summary>
    private const int startAngle = 135;

    /// <summary>
    /// The minimum distance that can be detected (in m).
    /// Based on the Hokuyo Lidar datasheet.
    /// </summary>
    private const float minRange = 0.02f;

    /// <summary>
    /// The value recorded for a sample less than minRange.
    /// </summary>
    private const float minCode = 0.0f;

    /// <summary>
    /// The maximum distance that can be detected (in m).
    /// Based on the Hokuyo Lidar datasheet.
    /// </summary>
    private const float maxRange = 10;

    /// <summary>
    /// The value recorded for a sample greater than maxRange.
    /// </summary>
    private const float maxCode = 0.0f;

    /// <summary>
    /// The average relative error of distance measurements.
    /// Based on the Hokuyo Lidar datasheet.
    /// </summary>
    private const float averageErrorFactor = 0.02f;

    /// <summary>
    /// The maximum range displayed in the LIDAR visualization (in m).
    /// </summary>
    private const float visualizationRange = 10;

    /// <summary>
    /// The Lidar visualization area on screen.
    /// </summary>
    public LidarHeatMap heatMap;
    #endregion

    #region Public Interface
    /// <summary>
    /// The distance (in cm) of each angle sample.
    /// </summary>
    public float[] Samples { get; private set; }

    /// <summary>
    /// Creates a visualization of the current LIDAR samples.
    /// </summary>
    /// <param name="texture">The texture to which the LIDAR visualization is rendered.</param>
    public void VisualizeLidar(Texture2D texture)
    {
        Unity.Collections.NativeArray<Color32> rawData = texture.GetRawTextureData<Color32>();

        // Create background: gray for in range and black for out of range
        int circleBoundary = Math.Min(texture.width, texture.height) * Math.Min(texture.width, texture.height) / 4;
        for (int r = 0; r < texture.height; r++)
        {
            for (int c = 0; c < texture.width; c++)
            {
                float x = r - texture.height / 2;
                float y = c - texture.width / 2;
                rawData[r * texture.width + c] = x * x + y * y < circleBoundary ? Hud.SensorBackgroundColor : Color.black;
            }
        }

        // Render each sample as a red pixel
        Vector2 center = new Vector2(texture.width / 2, texture.height / 2);
        float length = Mathf.Min(texture.width / 2.0f, texture.height / 2.0f);
        for (int i = 0; i < this.Samples.Length; i++)
        {
            if (this.Samples[i] < Lidar.visualizationRange * 100)
            {
                float angle = 2 * Mathf.PI * i / Lidar.NumSamples - Mathf.Deg2Rad * Lidar.startAngle;
                Vector2 point = center + this.Samples[i] / 100 / Lidar.visualizationRange * length * new Vector2(Mathf.Sin(angle), Mathf.Cos(angle));
                rawData[(int)point.y * texture.width + (int)point.x] = Color.red;
            }
        }

        texture.Apply();
    }
    #endregion

    /// <summary>
    /// The index of the most recently captured sample.
    /// </summary>
    private int curSample = 0;

    protected override void FindParent()
    {
        this.racecar = this.GetComponentInParent<Racecar>();
    }

    protected override void Awake()
    {
        base.Awake();
        this.Samples = new float[Lidar.NumSamples];
        heatMap = FindObjectOfType<LidarHeatMap>();
    }

    private void Update()
    {
        if (heatMap != null)
        {
            this.VisualizeLidar(heatMap.heatMapTexture);
        }
    }

    private void FixedUpdate()
    {
        int lastSample = (curSample + Mathf.RoundToInt(Lidar.samplesPerSecond * Time.fixedDeltaTime)) % NumSamples;

        // Take samples for the current frame by physically rotating the LIDAR
        while (curSample != lastSample)
        {
            float lidar_angle = curSample * 360.0f / Lidar.NumSamples;
            this.transform.localRotation = Quaternion.Euler(0, lidar_angle - startAngle, 0);
            // don't read the backward direction
            if (lidar_angle <= 270.25)
            {
                this.Samples[curSample] = TakeSample();
            } else {
                this.Samples[curSample] = 0;
            }
            curSample = (curSample + 1) % NumSamples;
        }
    }

    /// <summary>
    /// Take a sample at the current orientation.
    /// </summary>
    /// <returns>The distance (in cm) of the object directly in view of the LIDAR.</returns>
    private float TakeSample()
    {
        if (Physics.Raycast(this.transform.position, this.transform.forward, out RaycastHit raycastHit, Lidar.maxRange, Constants.IgnoreUIMask))
        {
            float distance = Settings.IsRealism 
                ? raycastHit.distance * NormalDist.Random(1, Lidar.averageErrorFactor)
                : raycastHit.distance;
            return distance > Lidar.minRange ? distance * 100 : Lidar.minCode;
        }

        return Lidar.maxCode;
    }

    /// <summary>
    /// Returns true if the forward direction is clear.
    /// </summary>
    /// <returns>True if the forward direction is clear, false otherwise.</returns>
    public bool IsForwardClear()
    {
        int forwardIndex = Lidar.startAngle * Lidar.NumSamples / 360;
        Debug.Log(forwardIndex);

        for (int i = forwardSampleRange; i <= forwardSampleRange; i++)
        {
            if (this.Samples[i] < clearDistanceThreshold)
            {
                return false;
            }
        }

        return true;
    }
}
