using System;
using NWH.WheelController3D;
using Unity.MLAgents;
using Unity.MLAgents.Policies;
using UnityEngine;

/// <summary>
/// Encapsulates a RACECAR-MN.
/// </summary>
public class Racecar : MonoBehaviour
{
    #region Set in Unity Editor
    /// <summary>
    /// The maximum speed of the car in m/s.
    /// </summary>
    public float maxSpeed = 5;

    /// <summary>
    /// The cameras through which the user can observe the car.
    /// </summary>
    [SerializeField]
    private Camera[] playerCameras;

    /// <summary>
    /// The front half of the car's chassis.
    /// </summary>
    [SerializeField]
    private GameObject chassisFront;

    /// <summary>
    /// The rear half of the car's chassis.
    /// </summary>
    [SerializeField]
    private GameObject chassisBack;
    #endregion

    #region Constants
    /// <summary>
    /// The distance from which each player camera follows the car.
    /// </summary>
    private static readonly Vector3[] cameraOffsets =
    {
        new Vector3(0, 0.7f, -1.3f),
        new Vector3(0, 1.5f, 0),
        new Vector3(0, 0.6f, 1.6f)
    };

    /// <summary>
    /// The speed at which the camera follows the car.
    /// </summary>
    private const float cameraSpeed = 6;
    #endregion

    #region Public Interface
    /// <summary>
    /// The index of the racecar.
    /// </summary>
    public int Index { get; private set; }

    /// <summary>
    /// Exposes the RealSense D435i color and depth channels.
    /// </summary>
    public CameraModule Camera { get; private set; }

    /// <summary>
    /// Exposes the car motors.
    /// </summary>
    public Drive Drive { get; private set; }

    /// <summary>
    /// Exposes the YDLIDAR X4 sensor.
    /// </summary>
    public Lidar Lidar { get; private set; }

    /// <summary>
    /// Exposes the RealSense D435i IMU.
    /// </summary>
    public PhysicsModule Physics { get; private set; }

    /// <summary>
    /// The heads-up display controlled by this car, if any.
    /// </summary>
    public Hud Hud { get; set; }

    /// <summary>
    /// Indicates whether the racecar has collided with an object.
    /// </summary>
    public bool Collided { get; set; } = false;

    private RacecarNWH carController;

    /// <summary>
    /// The center point of the car.
    /// </summary>
    public Vector3 Center
    {
        get
        {
            return this.transform.position + this.transform.up * 0.04f;
        }
    }

    /// <summary>
    /// Called on the first frame when the car enters default drive mode.
    /// </summary>
    public void DefaultDriveStart()
    {
        this.Drive.MaxSpeed = Drive.DefaultMaxSpeed;
        this.Drive.Stop();
    }

    #endregion

    /// <summary>
    /// The index in PlayerCameras of the current active camera.
    /// </summary>
    private int curCamera;

    private void Awake()
    {
        this.curCamera = 0;

        // Find submodules
        this.Camera = this.GetComponent<CameraModule>();
        this.Drive = this.GetComponent<Drive>();
        this.Lidar = this.GetComponentInChildren<Lidar>();
        this.Physics = this.GetComponent<PhysicsModule>();
        this.carController = this.GetComponent<RacecarNWH>();

        // Begin with main player camera (0th camera)
        if (this.playerCameras.Length > 0)
        {
            this.playerCameras[0].enabled = true;
            for (int i = 1; i < this.playerCameras.Length; i++)
            {
                this.playerCameras[i].enabled = false;
            }
        }

        DefaultDriveStart();
    }

    private void OnCollisionEnter(Collision collision)
    {
        // Check if the collided object is a wall
        if (collision.gameObject.CompareTag("Wall"))
        {
            // Debug.Log("Collision with wall");
            // Set the speed and angle to 0
            this.Drive.Angle = 0;
            this.Drive.Speed = 0;

            Collided = true;
        }
    }

    private void Update()
    {
        // Toggle camera when the space bar is pressed
        if (Input.GetKeyDown(KeyCode.Space))
        {
            this.playerCameras[this.curCamera].enabled = false;
            this.curCamera = (this.curCamera + 1) % this.playerCameras.Length;
            this.playerCameras[this.curCamera].enabled = true;
        }

        this.Drive.AngleK = Input.GetAxis("Horizontal");
        this.Drive.SpeedK = Input.GetAxis("Vertical");

        // Test out Lidar data:
        // Debug.Log(this.Lidar.Samples);
        // Test out Lidar isForward
        // Debug.Log(this.Lidar.IsForwardClear());
    }
    private void FixedUpdate()
    {
        Vector3 deltaVelocity = Physics.LinearAccceleration * Time.fixedDeltaTime;
        Vector3 predictedVelocity = Physics.LinearVelocity + deltaVelocity;
        if (predictedVelocity.z > maxSpeed)
        {
            float exceededAccel = (predictedVelocity.z - maxSpeed) / Time.fixedDeltaTime;
            float coefficient = Physics.LinearAccceleration.z / (Physics.LinearAccceleration.z - exceededAccel);
            carController.driveAxis = Mathf.Min(carController.driveAxis, coefficient);
        }
    }

    private void LateUpdate()
    {
        for (int i = 0; i < this.playerCameras.Length; i++)
        {
            Vector3 followPoint = this.transform.forward * Racecar.cameraOffsets[i].z;
            Vector3 targetCameraPosition = this.transform.position + new Vector3(followPoint.x, Racecar.cameraOffsets[i].y, followPoint.z);
            this.playerCameras[i].transform.position = Vector3.Lerp(
                this.playerCameras[i].transform.position,
                targetCameraPosition,
                Racecar.cameraSpeed * Time.deltaTime);

            this.playerCameras[i].transform.LookAt(this.transform.position);
        }
    }


}
