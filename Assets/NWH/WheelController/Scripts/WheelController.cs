using NWH.Common.Vehicles;
using System;
using UnityEngine;
using System.Collections.Generic;

#if UNITY_EDITOR
using UnityEditor;
using NWH.NUI;
#endif


namespace NWH.WheelController3D
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(100)]
    public partial class WheelController : WheelUAPI
    {
        [Tooltip("    Instance of the spring.")]
        [SerializeField]
        public Spring spring = new Spring();

        [Tooltip("    Instance of the damper.")]
        [SerializeField]
        public Damper damper = new Damper();

        [Tooltip("    Instance of the wheel.")]
        [SerializeField]
        public Wheel wheel = new Wheel();

        [Tooltip("    Side (lateral) friction info.")]
        [SerializeField]
        public Friction sideFriction = new Friction();

        [Tooltip("    Forward (longitudinal) friction info.")]
        [SerializeField]
        public Friction forwardFriction = new Friction();

        /// <summary>
        ///     Contains data about the ground contact point. 
        ///     Not valid if !_isGrounded.
        /// </summary>
        [Tooltip("    Contains point in which wheel touches ground. Not valid if !_isGrounded.")]
        [NonSerialized]
        private WheelHit wheelHit;

        /// <summary>
        ///     Current active friction preset.
        /// </summary>
        [Tooltip("    Current active friction preset.")]
        [SerializeField]
        private FrictionPreset activeFrictionPreset;

        /// <summary>
        ///     Motor torque applied to the wheel in Nm.
        ///     Can be positive or negative.
        /// </summary>
        [Tooltip(
            "Motor torque applied to the wheel. Since NWH Vehicle Physics 2 the value is readonly and setting it will have no effect\r\nsince torque calculation is done inside powertrain solver.")]
        private float motorTorque;

        /// <summary>
        ///     Brake torque applied to the wheel in Nm.
        ///     Must be positive.
        /// </summary>
        [Tooltip("    Brake torque applied to the wheel in Nm.")]
        private float brakeTorque;

        /// <summary>
        ///     The amount of torque returned by the wheel.
        ///     Under no-slip conditions this will be equal to the torque that was input.
        ///     When there is wheel spin, the value will be less than the input torque.
        /// </summary>
        [Tooltip("    The amount of torque returned by the wheel.\r\n    Under perfect grip conditions this will be equal to the torque that was put down.\r\n    While in air the value will be equal to the source torque minus torque that is result of dW of the wheel.")]
        private float counterTorque;

        /// <summary>
        ///     Current steer angle of the wheel, in deg.
        /// </summary>
        [Tooltip("    Current steer angle of the wheel.")]
        private float steerAngle;

        /// <summary>
        /// Current camber value.
        /// </summary>
        [SerializeField]
        private float camber;

        /// <summary>
        ///     Tire load in Nm.
        /// </summary>
        [Tooltip("    Tire load in Nm.")]
        [NonSerialized]
        private float load;

        /// <summary>
        ///     Maximum load the tire is rated for in [N]. 
        ///     Used to calculate friction. Default value is adequate for most cars but 
        ///     larger and heavier vehicles such as semi trucks will use higher values.
        ///     A good rule of the thumb is that this value should be 2x the Load (Debug tab) 
        ///     while vehicle is stationary.
        /// </summary>
        [SerializeField]
        private float loadRating = 5400;

        /// <summary>
        ///     Constant torque acting similar to brake torque.
        ///     Imitates rolling resistance.
        /// </summary>
        [Range(0, 500)]
        [Tooltip("    Constant torque acting similar to brake torque.\r\n    Imitates rolling resistance.")]
        public float rollingResistanceTorque = 30f;

        /// <summary>
        ///     Amount of anti-squat geometry. 
        ///     -1 = There is no anti-squat and full squat torque is applied to the chassis.
        ///     0 = No squat torque is applied to the chassis.
        ///     1 = Anti-squat torque (inverse squat) is applied to the chassis.
        ///     Higher value will result in less vehicle squat/dive under acceleration/braking.
        /// </summary>
        [Range(-1, 1)]
        [Tooltip("    Amount of anti-squat geometry. \r\n    " +
            "-1 = There is no anti-squat and full squat torque is applied to the chassis.\r\n    " +
            "0 = No squat torque is applied to the chassis.\r\n    " +
            "1 = Anti-squat torque (inverse squat) is applied to the chassis.\r\n    " +
            "Higher value will result in less vehicle squat/dive under acceleration/braking.")]
        public float antiSquat;

        /// <summary>
        /// Higher the number, higher the effect of longitudinal friction on lateral friction.
        /// If 1, when wheels are locked up or there is wheel spin it will be impossible to steer.
        /// If 0 doughnuts or power slides will be impossible.
        /// The 'accurate' value is 1 but might not be desirable for arcade games.
        /// </summary>
        [Tooltip("Higher the number, higher the effect of longitudinal friction on lateral friction.\r\n" +
            "If 1, when wheels are locked up or there is wheel spin it will be impossible to steer." +
            "\r\nIf 0 doughnuts or power slides will be impossible.\r\n" +
            "The 'accurate' value is 1 but might not be desirable for arcade games.")]
        [Range(0, 1)]
        [SerializeField]
        private float frictionCircleStrength = 1f;

        /// <summary>
        /// Higher values have more pronounced slip circle effect as the lateral friction will be
        /// decreased with smaller amounts of longitudinal slip (wheel spin).
        /// Realistic is ~1.5-2.
        /// </summary>
        [Range(0.0001f, 3f)]
        [SerializeField]
        [Tooltip("Higher values have more pronounced slip circle effect as the lateral friction will be\r\ndecreased with smaller amounts of longitudinal slip (wheel spin).\r\nRealistic is ~1.5-2.")]
        private float frictionCircleShape = 0.9f;

        /// <summary>
        ///     True if wheel touching ground.
        /// </summary>
        [Tooltip("    True if wheel touching ground.")]
        private bool _isGrounded;

        /// <summary>
        ///     Rigidbody to which the forces will be applied.
        /// </summary>
        [Tooltip("    Rigidbody to which the forces will be applied.")]
        [SerializeField]
        private Rigidbody targetRigidbody;

        /// <summary>
        /// Distance as a percentage of the max spring length. Value of 1 means that the friction force will
        /// be applied 1 max spring length above the contact point, and value of 0 means that it will be applied at the
        /// ground level. Value can be >1.
        /// Can be used instead of the anti-roll bar to prevent the vehicle from tipping over in corners
        /// and can be useful in low framerate applications where anti-roll bar might induce jitter.
        /// </summary>
        [Tooltip("Distance as a percentage of the max spring length. Value of 1 means that the friction force will\r\nbe applied 1 max spring length above the contact point, and value of 0 means that it will be applied at the\r\nground level. Value can be >1.\r\nCan be used instead of the anti-roll bar to prevent the vehicle from tipping over in corners\r\nand can be useful in low framerate applications where anti-roll bar might induce jitter.")]
        public float forceApplicationPointDistance = 0.8f;

        /// <summary>
        /// Disables the motion vectors on the wheel visual to prevent artefacts due to 
        /// the wheel rotation when using PostProcessing.
        /// </summary>
        [Tooltip("Disables the motion vectors on the wheel visual to prevent artefacts due to \r\nthe wheel rotation when using PostProcessing.")]
        public bool disableMotionVectors = true;

        /// <summary>
        /// The speed coefficient of the spring / suspension extension when not on the ground.
        /// wheel.perceivedPowertrainInertia.e. how fast the wheels extend when in the air.
        /// The setting of 1 will result in suspension fully extending in 1 second, 2 in 0.5s, 3 in 0.333s, etc.
        /// Recommended value is 6-10.
        /// </summary>
        [Range(0.01f, 30f)]
        [Tooltip("The speed coefficient of the spring / suspension extension when not on the ground.\r\nwheel.perceivedPowertrainInertia.e. how fast the wheels extend when in the air.\r\nThe setting of 1 will result in suspension fully extending in 1 second, 2 in 0.5s, 3 in 0.333s, etc.\r\nRecommended value is 6-10.")]
        public float suspensionExtensionSpeedCoeff = 6f;

        /// <summary>
        /// The amount of wobble around the X-axis the wheel will have when fully damaged.
        /// Part of the damage visualization and does not affect handling.
        /// </summary>
        [Range(0f, 90f)]
        [Tooltip("The amount of wobble around the X-axis the wheel will have when fully damaged.\r\nPart of the damage visualization and does not affect handling.")]
        public float damageMaxWobbleAngle = 30f;

        /// <summary>
        /// Scales the forces applied to other Rigidbodies. Useful for interacting
        /// with lightweight objects and prevents them from flying away or glitching out.
        /// </summary>
        [Tooltip("Scales the forces applied to other Rigidbodies. Useful for interacting\r\nwith lightweight objects and prevents them from flying away or glitching out.")]
        public float otherBodyForceScale = 1f;

        /// <summary>
        /// The percentage this wheel is contributing to the total vehicle load bearing.
        /// </summary>
        public float loadContribution = 0.25f;


        /// <summary>
        /// Layers that will be detected by the wheel cast.
        /// </summary>
        public LayerMask layerMask = 1 << 0;


        /// <summary>
        /// Layer the mesh collider of the wheel is on.
        /// </summary>
        public int meshColliderLayer = 2;


        private bool _autoSimulate = true;
        private Vector3 _hitLocalPoint;
        private Vector3 _hitContactVelocity;
        private Vector3 _hitSurfaceVelocity;
        private Vector3 _hitForwardDirection;
        private Vector3 _hitSidewaysDirection;
        private Rigidbody _hitRigidbody;
        private Vector3 _frictionForce;
        private Vector3 _suspensionForce;
        private float _damage;
        private Transform _transform;
        private bool _initialized;
        private float _dt;
        private Vector3 _transformPosition;
        private Quaternion _transformRotation;
        private Vector3 _transformUp;
        private Vector3 _zeroVector;
        private Vector3 _upVector;
        private Vector3 _forwardVector;
        private Vector3 _rightVector;
        private Quaternion _localSteerRotation;
        private Quaternion _localAxleRotation;
        private Quaternion _localDamageRotation;
        private Quaternion _localBaseRotation;
        private Quaternion _worldBaseRotation;
        private Quaternion _camberRotation;
        private GroundDetectionBase _groundDetection;
        private List<int> _initColliderLayers;
        private List<GameObject> _vehicleColliderObjects;
        private int _vehicleColliderObjectCount;
        private WheelControllerManager _wheelControllerManager;
        private bool _lowSpeedReferenceIsSet;
        private Vector3 _lowSpeedReferencePosition;


        private void Awake()
        {
            // Find the target Rigidbody if not already assigned
            if (targetRigidbody == null)
            {
                targetRigidbody = GetComponentInParent<Rigidbody>();
            }
            Debug.Assert(targetRigidbody != null, $"Parent Rigidbody not found on {name}.");
        }


        private void Start()
        {
            // Show a warning if Time.fixedDeltaTime is low
            ShowDtWarning();

            // Find (or add) the wheel manager
            FindOrAddWheelControllerManager();

            // Cache frequently used values
            _transform = transform;
            _dt = Time.fixedDeltaTime;
            _zeroVector = Vector3.zero;
            _upVector = Vector3.up;
            _forwardVector = Vector3.forward;
            _rightVector = Vector3.right;

            // Sets the defaults if needed.
            SetRuntimeDefaults();

            // Disable motion vectors to avoid issues with PP blur.
            DisableMotionVectors();

            // Initialize the wheel
            wheel.Initialize(this);

            // Initialize spring length to starting value.
            if (spring.maxLength > 0) spring.length = -_transform.InverseTransformPoint(wheel.visualTransform.position).y;

            // Initialize ground detection
            _groundDetection = GetComponent<GroundDetectionBase>();
            if (_groundDetection == null) _groundDetection = gameObject.AddComponent<StandardGroundDetection>();
            wheelHit = new WheelHit();

            // Initialize layers for casting. Used to prevent the rays from hitting the vehicle itself
            InitializeVehicleLayers();

            // Initialization done, wheel can be updated now
            _initialized = true;
        }


        private void FixedUpdate()
        {
            if (_autoSimulate)
            {
                Step();
            }
        }


        private void OnEnable()
        {
            RegisterWithWheelControllerManager();
        }


        private void OnDisable()
        {
            DeregisterWithWheelControllerManager();
        }


        public void InitializeVehicleLayers()
        {
            // Initialize layers
            _vehicleColliderObjects = new List<GameObject>();
            _initColliderLayers = new List<int>();

            Collider[] colliders = targetRigidbody.gameObject.GetComponentsInChildren<Collider>();
            foreach (Collider c in colliders)
            {
                GameObject go = c.gameObject;
                if (go.layer == 2) continue;
                _vehicleColliderObjects.Add(go);
                _initColliderLayers.Add(go.layer);
            }
            _vehicleColliderObjectCount = _vehicleColliderObjects.Count;
        }


        public override void Step()
        {
            if (!_initialized || !isActiveAndEnabled) return;

            // Cache values
            _dt = Time.fixedDeltaTime;

            // Ensure that parameters are within valid ranges to avoid NaN
            if (_dt < 1e-6f) _dt = 1e-6f;
            if (wheel.radius < 1e-6f) wheel.radius = 1e-6f;
            if (wheel.inertia < 1e-6f) wheel.inertia = 1e-6f;

            // Optimization. Ideally visual should be a Transform but backwards compatibility is required.
            wheel.visualTransform = wheel.visual.transform;
            wheel.colliderTransform = wheel.colliderGO.transform;

            // Update cached and previous values
            _transformPosition = _transform.position;
            _transformRotation = _transform.rotation;
            _transformUp = _transform.up;
            wheel.prevWorldPosition = wheel.worldPosition;
            wheel.prevAngularVelocity = wheel.angularVelocity;
            spring.prevLength = spring.length;
            spring.prevVelocity = spring.compressionVelocity;

            wheel.CheckForWheelDimensionChange();

            _isGrounded = FindTheHitPoint();

            bool bottomMeshColliderEnabled = false;

            // Check for hit above axle and enable the collider if there is one
            bool hitAboveAxle = _hitLocalPoint.y > wheel.localPosition.y;
            if (_isGrounded && hitAboveAxle)
            {
                bottomMeshColliderEnabled = true;
            }

            // Check for high vertical velocity and enable the collider if above one frame travel distance
            float thresholdVelocity = spring.maxLength < 1e-5f ? -Mathf.Infinity : -spring.maxLength / _dt;
            float relativeYVelocity = transform.InverseTransformVector(targetRigidbody.velocity).y;
            if (relativeYVelocity < thresholdVelocity)
            {
                bottomMeshColliderEnabled = true;
            }


            if (!bottomMeshColliderEnabled)
            {
                UpdateSpringAndDamper();
                bottomMeshColliderEnabled = spring.extensionState == Spring.ExtensionState.BottomedOut;
            }

            wheel.bottomMeshCollider.enabled = bottomMeshColliderEnabled;

            UpdateWheelValues();
            UpdateHitVariables();
            UpdateFriction();
            ApplySquatAndChassisTorque();
            ApplyForceToHitBody();
        }



        private bool FindTheHitPoint()
        {
            // Find the hit point
            Vector3 origin;
            Vector3 direction;
            float length;

            bool hasSuspension = spring.maxLength > 0f;
            float offset = hasSuspension ? wheel.radius * 1.1f : wheel.radius * 0.1f;
            length = hasSuspension ? wheel.radius * 2.2f + spring.maxLength : wheel.radius * 0.02f + offset;

            origin.x = _transformPosition.x + _transformUp.x * offset;
            origin.y = _transformPosition.y + _transformUp.y * offset;
            origin.z = _transformPosition.z + _transformUp.z * offset;

            direction.x = -_transformUp.x;
            direction.y = -_transformUp.y;
            direction.z = -_transformUp.z;

            SetColliderLayersToIgnore();
            bool hasHit = _groundDetection.WheelCast(origin, direction, length, wheel.radius, wheel.width,
                ref wheelHit, layerMask);
            ResetColliderLayers();

            if (hasHit)
            {
                _hitLocalPoint = _transform.InverseTransformPoint(wheelHit.point);
            }

            return hasHit;
        }


        private void UpdateSpringAndDamper()
        {
            float localAirYPosition = wheel.localPosition.y - _dt * spring.maxLength * suspensionExtensionSpeedCoeff;

            if (_isGrounded)
            {
                float zDistance = _hitLocalPoint.z;
                float sine = zDistance / wheel.radius;
                sine = sine > 1f ? 1f : sine < -1f ? -1f : sine;
                float hitAngle = Mathf.Asin(sine);
                float localGroundedYPosition = _hitLocalPoint.y + wheel.radius * Mathf.Cos(hitAngle);
                wheel.localPosition.y = localGroundedYPosition > localAirYPosition
                    ? localGroundedYPosition
                    : localAirYPosition;
            }
            else
            {
                wheel.localPosition.y = localAirYPosition;
            }

            spring.length = -wheel.localPosition.y;

            if (spring.length <= 0f || spring.maxLength == 0f)
            {
                spring.extensionState = Spring.ExtensionState.BottomedOut;
                spring.length = 0;
            }
            else if (spring.length >= spring.maxLength)
            {
                spring.extensionState = Spring.ExtensionState.OverExtended;
                spring.length = spring.maxLength;
                _isGrounded = false;
            }
            else
            {
                spring.extensionState = Spring.ExtensionState.Normal;
            }

            spring.compressionVelocity = (spring.prevLength - spring.length) / _dt;
            spring.compression = spring.maxLength == 0 ? 1f : (spring.maxLength - spring.length) / spring.maxLength;
            spring.force = _isGrounded ? spring.maxForce * spring.forceCurve.Evaluate(spring.compression) : 0f;
            damper.force = _isGrounded ? damper.CalculateDamperForce(spring.compressionVelocity) : 0f;

            if (_isGrounded)
            {
                if (spring.maxLength > 0f)
                {
                    load = spring.force + damper.force;
                    load = load < 0f ? 0f : load;
                    _suspensionForce.x = load * wheelHit.normal.x;
                    _suspensionForce.y = load * wheelHit.normal.y;
                    _suspensionForce.z = load * wheelHit.normal.z;
                    targetRigidbody.AddForceAtPosition(_suspensionForce, _transformPosition);
                }
                else
                {
                    load = loadRating;
                    _suspensionForce = _zeroVector;
                }
            }
            else
            {
                load = 0;
                _suspensionForce = _zeroVector;
            }
        }


        private void UpdateHitVariables()
        {
            if (_isGrounded)
            {
                _hitContactVelocity = targetRigidbody.GetPointVelocity(wheelHit.point);
                _hitForwardDirection = Vector3.Normalize(Vector3.Cross(wheelHit.normal, -wheel.right));
                _hitSidewaysDirection = Quaternion.AngleAxis(90f, wheelHit.normal) * _hitForwardDirection;
                _hitRigidbody = wheelHit.collider?.attachedRigidbody;

                if (_hitRigidbody != null)
                {
                    _hitSurfaceVelocity = _hitRigidbody.GetPointVelocity(wheelHit.point);
                    _hitContactVelocity -= _hitSurfaceVelocity;
                }
                else
                {
                    _hitSurfaceVelocity = _zeroVector;
                }

                // Get forward and side friction speed components
                forwardFriction.speed = Vector3.Dot(_hitContactVelocity, _hitForwardDirection);
                sideFriction.speed = Vector3.Dot(_hitContactVelocity, _hitSidewaysDirection);
            }
            else
            {
                forwardFriction.speed = 0f;
                sideFriction.speed = 0f;
            }
        }


        /// <summary>
        /// Updates the wheel positions and rotations.
        /// </summary>
        private void UpdateWheelValues()
        {
            // Update wheel position
            wheel.localPosition.y = -spring.length;
            wheel.worldPosition = _transform.TransformPoint(wheel.localPosition);

            // Update rotations
            float localXPosition = _transform.localPosition.x;
            float camberAngle = camber * (localXPosition < 0 ? 1f : -1f);
            _camberRotation = Quaternion.AngleAxis(camberAngle, _forwardVector);

            wheel.axleAngle = wheel.axleAngle % 360.0f + wheel.angularVelocity * Mathf.Rad2Deg * _dt;
            _localSteerRotation = Quaternion.AngleAxis(steerAngle, _upVector);
            _localAxleRotation = Quaternion.AngleAxis(wheel.axleAngle, _rightVector);
            _localDamageRotation = Quaternion.AngleAxis(_damage * damageMaxWobbleAngle, _upVector);

            _localBaseRotation = _localDamageRotation * _localSteerRotation * _camberRotation;
            _worldBaseRotation = _transformRotation * _localBaseRotation;
            wheel.localRotation = _localBaseRotation * _localAxleRotation;
            wheel.worldRotation = _transformRotation * wheel.localRotation;

            // Update directions
            wheel.up = _worldBaseRotation * _upVector;
            wheel.forward = _worldBaseRotation * _forwardVector;
            wheel.right = _worldBaseRotation * _rightVector;

            // Apply transforms
            wheel.visualTransform.SetPositionAndRotation(wheel.worldPosition, wheel.worldRotation);
            wheel.colliderTransform.SetPositionAndRotation(wheel.worldPosition, _worldBaseRotation);

            if (wheel.nonRotatingVisual != null)
            {
                Vector3 position = wheel.visualTransform.position + _worldBaseRotation * wheel.nonRotatingVisualPositionOffset;
                Quaternion rotation = _worldBaseRotation * wheel.nonRotatingVisualRotationOffset;
                wheel.nonRotatingVisual.transform.SetPositionAndRotation(position, rotation);
            }
        }


        protected virtual void UpdateFriction()
        {
            counterTorque = 0;
            forwardFriction.force = 0;
            sideFriction.force = 0;

            if (activeFrictionPreset.BCDE.z < 1e-5f)
            {
                activeFrictionPreset.BCDE.z = 1e-5f;
            }

            float allWheelLoadSum = _wheelControllerManager.combinedLoad;
            loadContribution = allWheelLoadSum == 0 ? 1f : load / allWheelLoadSum;

            float invDt = 1f / _dt;
            float invRadius = 1f / wheel.radius;
            float inertia = wheel.inertia;
            float invInertia = 1f / wheel.inertia;

            float loadClamped = load < 0f ? 0f : load > loadRating ? loadRating : load;
            float forwardLoadFactor = loadClamped * 1.35f;
            float sideLoadFactor = loadClamped * 1.9f;

            float loadPercent = load / loadRating;
            loadPercent = loadPercent < 0f ? 0f : loadPercent > 1f ? 1f : loadPercent;
            float slipLoadModifier = 1f - loadPercent * 0.4f;

            float mass = targetRigidbody.mass;
            float absForwardSpeed = forwardFriction.speed < 0 ? -forwardFriction.speed : forwardFriction.speed;
            float forwardForceClamp = mass * loadContribution * absForwardSpeed * invDt;
            float absSideSpeed = sideFriction.speed < 0 ? -sideFriction.speed : sideFriction.speed;
            float sideForceClamp = mass * loadContribution * absSideSpeed * invDt;

            float forwardSpeedClamp = 1.5f * (_dt / 0.005f);
            forwardSpeedClamp = forwardSpeedClamp < 1.5f ? 1.5f : forwardSpeedClamp > 10f ? 10f : forwardSpeedClamp;
            float clampedAbsForwardSpeed = absForwardSpeed < forwardSpeedClamp ? forwardSpeedClamp : absForwardSpeed;

            // Calculate effect of camber on friction
            float camberFrictionCoeff = Vector3.Dot(wheel.up, wheelHit.normal);
            camberFrictionCoeff = camberFrictionCoeff < 0f ? 0f : camberFrictionCoeff;


            // *******************************
            // ******** LONGITUDINAL ********* 
            // *******************************
            // In this version of the friction friction itself and angular velocity are independent.
            // This results in a somewhat reduced physical accuracy and ignores the tail end of the friction curve
            // but gives better results overall with the most common physics update rates (33Hz - 100Hz) since
            // there is no circular dependency between the angular velocity / slip and force which makes it stable
            // and removes the need for iterative methods. Since the stable state is achieved within one frame it can run 
            // with as low as needed physics update.

            // T = r * F
            // F = T / r;

            // *** FRICTION ***
            float peakForwardFrictionForce = activeFrictionPreset.BCDE.z * forwardLoadFactor * forwardFriction.grip;
            float absCombinedBrakeTorque = brakeTorque + rollingResistanceTorque;
            absCombinedBrakeTorque = absCombinedBrakeTorque < 0 ? 0 : absCombinedBrakeTorque;
            float signedCombinedBrakeTorque = absCombinedBrakeTorque * (forwardFriction.speed < 0 ? 1f : -1f);
            float signedCombinedBrakeForce = signedCombinedBrakeTorque * invRadius;
            float motorForce = motorTorque * invRadius;
            float forwardInputForce = motorForce + signedCombinedBrakeForce;
            float absMotorTorque = motorTorque < 0 ? -motorTorque : motorTorque;
            float absBrakeTorque = brakeTorque < 0 ? -brakeTorque : brakeTorque;
            float maxForwardForce = peakForwardFrictionForce < forwardForceClamp ? peakForwardFrictionForce : forwardForceClamp;
            maxForwardForce = absMotorTorque < absBrakeTorque ? maxForwardForce : peakForwardFrictionForce;
            forwardFriction.force = forwardInputForce > maxForwardForce ? maxForwardForce
                : forwardInputForce < -maxForwardForce ? -maxForwardForce : forwardInputForce;


            // *** ANGULAR VELOCITY ***

            // Brake and motor (corruptive) force
            bool wheelIsBlocked = false;
            if (_isGrounded)
            {
                float absCombinedBrakeForce = absCombinedBrakeTorque * invRadius;
                float brakeForceSign = wheel.angularVelocity < 0 ? 1f : -1f;
                float signedWheelBrakeForce = absCombinedBrakeForce * brakeForceSign;
                float combinedWheelForce = motorForce + signedWheelBrakeForce;
                float wheelForceClampOverflow = 0;
                if ((combinedWheelForce >= 0 && wheel.angularVelocity < 0)
                    || (combinedWheelForce < 0 && wheel.angularVelocity > 0))
                {
                    float absAngVel = wheel.angularVelocity < 0 ? -wheel.angularVelocity : wheel.angularVelocity;
                    float absWheelForceClamp = absAngVel * inertia * invRadius * invDt;
                    float absCombinedWheelForce = combinedWheelForce < 0 ? -combinedWheelForce : combinedWheelForce;
                    float combinedWheelForceSign = combinedWheelForce < 0 ? -1f : 1f;
                    float wheelForceDiff = absCombinedWheelForce - absWheelForceClamp;
                    float clampedWheelForceDiff = wheelForceDiff < 0f ? 0f : wheelForceDiff;
                    wheelForceClampOverflow = clampedWheelForceDiff * combinedWheelForceSign;
                    combinedWheelForce = combinedWheelForce < -absWheelForceClamp ? -absWheelForceClamp :
                        combinedWheelForce > absWheelForceClamp ? absWheelForceClamp : combinedWheelForce;
                }
                wheel.angularVelocity += combinedWheelForce * wheel.radius * invInertia * _dt;

                // Surface (corrective) force
                float noSlipAngularVelocity = forwardFriction.speed * invRadius;
                float angularVelocityError = wheel.angularVelocity - noSlipAngularVelocity;
                float angularVelocityCorrectionForce = -angularVelocityError * inertia * invRadius * invDt;
                angularVelocityCorrectionForce = angularVelocityCorrectionForce < -maxForwardForce ? -maxForwardForce :
                    angularVelocityCorrectionForce > maxForwardForce ? maxForwardForce : angularVelocityCorrectionForce;

                float absWheelForceClampOverflow = wheelForceClampOverflow < 0 ? -wheelForceClampOverflow : wheelForceClampOverflow;
                float absAngularVelocityCorrectionForce = angularVelocityCorrectionForce < 0 ? -angularVelocityCorrectionForce : angularVelocityCorrectionForce;
                if (absMotorTorque < absBrakeTorque && absWheelForceClampOverflow > absAngularVelocityCorrectionForce)
                {
                    wheelIsBlocked = true;
                    wheel.angularVelocity = wheel.angularVelocity + forwardFriction.speed > 0 ? 1e-10f : -1e-10f;
                }
                else
                {
                    wheel.angularVelocity += angularVelocityCorrectionForce * wheel.radius * invInertia * _dt;
                }
            }
            else
            {
                float maxBrakeTorque = wheel.angularVelocity * inertia * invDt + motorTorque;
                maxBrakeTorque = maxBrakeTorque < 0 ? -maxBrakeTorque : maxBrakeTorque;
                float brakeTorqueSign = wheel.angularVelocity < 0f ? -1f : 1f;
                float clampedBrakeTorque = absCombinedBrakeTorque > maxBrakeTorque ? maxBrakeTorque :
                    absCombinedBrakeTorque < -maxBrakeTorque ? -maxBrakeTorque : absCombinedBrakeTorque;
                wheel.angularVelocity += (motorTorque - brakeTorqueSign * clampedBrakeTorque) * invInertia * _dt;
            }


            float absAngularVelocity = wheel.angularVelocity < 0 ? -wheel.angularVelocity : wheel.angularVelocity;

            // Powertrain counter torque
            counterTorque = (signedCombinedBrakeForce - forwardFriction.force) * wheel.radius;
            float maxCounterTorque = inertia * absAngularVelocity;
            counterTorque = Mathf.Clamp(counterTorque, -maxCounterTorque, maxCounterTorque);

            // Calculate slip based on the corrected angular velocity
            forwardFriction.slip = (forwardFriction.speed - wheel.angularVelocity * wheel.radius) / clampedAbsForwardSpeed;
            forwardFriction.slip *= forwardFriction.stiffness * slipLoadModifier;



            // *******************************
            // ********** LATERAL ************ 
            // *******************************

            sideFriction.slip = (Mathf.Atan2(sideFriction.speed, clampedAbsForwardSpeed) * Mathf.Rad2Deg) * 0.01111f;
            sideFriction.slip *= sideFriction.stiffness * slipLoadModifier;
            float sideSlipSign = sideFriction.slip < 0 ? -1f : 1f;
            float absSideSlip = sideFriction.slip < 0 ? -sideFriction.slip : sideFriction.slip;
            float peakSideFrictionForce = activeFrictionPreset.BCDE.z * sideLoadFactor * sideFriction.grip;
            float sideForce = -sideSlipSign * activeFrictionPreset.Curve.Evaluate(absSideSlip) * sideLoadFactor * sideFriction.grip;
            sideFriction.force = sideForce > sideForceClamp ? sideForce : sideForce < -sideForceClamp ? -sideForceClamp : sideForce;
            sideFriction.force *= camberFrictionCoeff;



            // *******************************
            // ******* ANTI - CREEP **********
            // *******************************

            // Get the error to the reference point and apply the force to keep the wheel at that point
            if (_isGrounded && absForwardSpeed < 0.12f && absSideSpeed < 0.12f)
            {
                float verticalOffset = spring.length + wheel.radius;
                Vector3 currentPosition;
                currentPosition.x = _transformPosition.x - _transformUp.x * verticalOffset;
                currentPosition.y = _transformPosition.y - _transformUp.y * verticalOffset;
                currentPosition.z = _transformPosition.z - _transformUp.z * verticalOffset;

                if (!_lowSpeedReferenceIsSet)
                {
                    _lowSpeedReferenceIsSet = true;
                    _lowSpeedReferencePosition = currentPosition;
                }
                else
                {
                    Vector3 referenceError;
                    referenceError.x = _lowSpeedReferencePosition.x - currentPosition.x;
                    referenceError.y = _lowSpeedReferencePosition.y - currentPosition.y;
                    referenceError.z = _lowSpeedReferencePosition.z - currentPosition.z;

                    Vector3 correctiveForce;
                    correctiveForce.x = invDt * loadContribution * mass * referenceError.x;
                    correctiveForce.y = invDt * loadContribution * mass * referenceError.y;
                    correctiveForce.z = invDt * loadContribution * mass * referenceError.z;

                    if (wheelIsBlocked && absAngularVelocity < 0.5f)
                    {
                        forwardFriction.force += Vector3.Dot(correctiveForce, _hitForwardDirection);
                    }

                    sideFriction.force += Vector3.Dot(correctiveForce, _hitSidewaysDirection);
                }
            }
            else
            {
                _lowSpeedReferenceIsSet = false;
            }


            // Clamp the forces once again, this time ignoring the force clamps as the anti-creep forces do not cause jitter,
            // so the forces are limited only by the surface friction.
            forwardFriction.force = forwardFriction.force > peakForwardFrictionForce ? peakForwardFrictionForce
                : forwardFriction.force < -peakForwardFrictionForce ? -peakForwardFrictionForce : forwardFriction.force;

            sideFriction.force = sideFriction.force > peakSideFrictionForce ? peakSideFrictionForce
                : sideFriction.force < -peakSideFrictionForce ? -peakSideFrictionForce : sideFriction.force;



            // *******************************
            // ********* SLIP CIRCLE ********* 
            // *******************************
            if (frictionCircleStrength > 0 && (absForwardSpeed > 2f || absAngularVelocity > 4f))
            {
                float forwardSlipPercent = forwardFriction.slip / activeFrictionPreset.peakSlip;
                float sideSlipPercent = sideFriction.slip / activeFrictionPreset.peakSlip;
                float slipCircleLimit = Mathf.Sqrt(forwardSlipPercent * forwardSlipPercent + sideSlipPercent * sideSlipPercent);
                if (slipCircleLimit > 1f)
                {
                    float beta = Mathf.Atan2(sideSlipPercent, forwardSlipPercent * frictionCircleShape);
                    float sinBeta = Mathf.Sin(beta);
                    float cosBeta = Mathf.Cos(beta);

                    float absForwardForce = forwardFriction.force < 0 ? -forwardFriction.force : forwardFriction.force;
                    float absSideForce = sideFriction.force < 0 ? -sideFriction.force : sideFriction.force;
                    float f = absForwardForce * cosBeta * cosBeta + absSideForce * sinBeta * sinBeta;

                    float invSlipCircleCoeff = 1f - frictionCircleStrength;
                    forwardFriction.force = invSlipCircleCoeff * forwardFriction.force - frictionCircleStrength * f * cosBeta;
                    sideFriction.force = invSlipCircleCoeff * sideFriction.force - frictionCircleStrength * f * sinBeta;
                }
            }


            // Apply the forces
            if (_isGrounded)
            {
                _frictionForce.x = _hitSidewaysDirection.x * sideFriction.force + _hitForwardDirection.x * forwardFriction.force;
                _frictionForce.y = _hitSidewaysDirection.y * sideFriction.force + _hitForwardDirection.y * forwardFriction.force;
                _frictionForce.z = _hitSidewaysDirection.z * sideFriction.force + _hitForwardDirection.z * forwardFriction.force;

                // Avoid adding calculated friction when using native friction
                Vector3 forcePosition;
                forcePosition.x = wheelHit.point.x + _transformUp.x * forceApplicationPointDistance * spring.maxLength;
                forcePosition.y = wheelHit.point.y + _transformUp.y * forceApplicationPointDistance * spring.maxLength;
                forcePosition.z = wheelHit.point.z + _transformUp.z * forceApplicationPointDistance * spring.maxLength;
                targetRigidbody.AddForceAtPosition(_frictionForce, forcePosition);
            }
            else
            {
                _frictionForce = _zeroVector;
            }
        }


        private void ApplySquatAndChassisTorque()
        {
            float squatMagnitude = forwardFriction.force * wheel.radius * antiSquat;
            Vector3 squatTorque;
            squatTorque.x = squatMagnitude * wheel.right.x;
            squatTorque.y = squatMagnitude * wheel.right.y;
            squatTorque.z = squatMagnitude * wheel.right.z;

            // Use base inertia here as the powertrain component orientation is not known and it might not contribute to the 
            // torque around the X-axis.
            float chassisTorqueMag = ((wheel.prevAngularVelocity - wheel.angularVelocity) * wheel.baseInertia) / _dt;
            Vector3 chassisTorque;
            chassisTorque.x = chassisTorqueMag * wheel.right.x;
            chassisTorque.y = chassisTorqueMag * wheel.right.y;
            chassisTorque.z = chassisTorqueMag * wheel.right.z;

            Vector3 combinedTorque;
            combinedTorque.x = squatTorque.x + chassisTorque.x;
            combinedTorque.y = squatTorque.y + chassisTorque.y;
            combinedTorque.z = squatTorque.z + chassisTorque.z;

            targetRigidbody.AddTorque(squatTorque + chassisTorque);
        }


        private void ApplyForceToHitBody()
        {
            if (_isGrounded)
            {
                if (_hitRigidbody != null)
                {
                    Vector3 totalForce;
                    totalForce.x = -(_frictionForce.x + _suspensionForce.x) * otherBodyForceScale;
                    totalForce.y = -(_frictionForce.y + _suspensionForce.y) * otherBodyForceScale;
                    totalForce.z = -(_frictionForce.z + _suspensionForce.z) * otherBodyForceScale;

                    _hitRigidbody.AddForceAtPosition(totalForce, wheelHit.point);
                }
            }
        }



        private void OnValidate()
        {
            // Check scale
            Debug.Assert(transform.localScale == Vector3.one,
                $"{name}: WheelController scale is not 1. WheelController scale should be [1,1,1].");

            // Check the visual
            if (wheel.visual == gameObject)
            {
                Debug.LogError($"{name}: Visual and WheelController are the same GameObject. This will result in unknown behaviour." +
                    $"The controller and the visual should be separate GameObjects.");
            }

            // Check for existing colliders
            if (!Application.isPlaying && wheel.visual != null && wheel.visual.GetComponentsInChildren<Collider>().Length > 0)
            {
                Debug.LogWarning($"{name}: Visual object already contains a Collider. Visual should have no colliders attached to it or its children" +
                    $" as they can prevent the wheel from functioning properly.");
            }

            if (targetRigidbody == null)
            {
                targetRigidbody = GetComponentInParent<Rigidbody>();
            }

            if (targetRigidbody != null)
            {
                string prefix = $"{targetRigidbody.name} > {name}:";

                // Check parent scale
                Debug.Assert(transform.localScale == Vector3.one, $"{prefix} WheelController parent Rigidbody scale is not 1. Rigidbody transform scale should be [1,1,1].");

                // Load rating
                float minLoadRating = targetRigidbody.mass * -Physics.gravity.y * 0.05f;
                float maxLoadRating = targetRigidbody.mass * -Physics.gravity.y * 4f;
                if (loadRating < minLoadRating)
                {
                    Debug.LogWarning($"{prefix} Load rating of the tyre might be too low. This can cause the vehicle to slide around. Current: {loadRating}, min. recommended: {minLoadRating}.");
                }
                else if (loadRating > maxLoadRating)
                {
                    Debug.LogWarning($"{prefix} Load rating of the tyre might be too high. This can cause the vehicle friction to not work properly. Current: {loadRating}, max. recommended: {maxLoadRating}.");
                }

                // Has suspension
                if (spring.length > 0)
                {
                    float minForce = targetRigidbody.mass * -Physics.gravity.y * 0.25f;
                    if (spring.maxForce < minForce)
                    {
                        Debug.LogWarning($"{prefix} spring.maxForce is most likely too low for the given Rigidbody mass. Current: {spring.maxForce}, min. recommended: {minForce}, recommended: {minForce * 3f}" +
                            $"With the current values the suspension might not be strong enough to support the weight of the vehicle and might bottom out.");
                    }

                    float minLength = Time.fixedDeltaTime;
                    if (spring.maxLength < minLength)
                    {
                        Debug.LogWarning($"{prefix} spring.maxLength is shorter than recommended for the given Time.fixedDeltaTime. Current: {spring.maxLength}, min. recommended: {minLength}. With " +
                            $"the current values the suspension might bottom out frequently and cause a harsh ride.");
                    }

                    // TODO - validate damper
                }
            }
            else
            {
                Debug.LogWarning($"Target Rigidbody on {name} is null!");
            }
        }


        /// <summary>
        /// Sets the body colliders to ignore raycast to prevent ray-vehicle interaction.
        /// </summary>
        private void SetColliderLayersToIgnore()
        {
            for (int i = 0; i < _vehicleColliderObjectCount; i++)
            {
                _vehicleColliderObjects[i].layer = 2;
            }
        }


        /// <summary>
        /// Reverts the body colliders to their original layers after SetColliderLayersToIgnore()
        /// </summary>
        private void ResetColliderLayers()
        {
            for (int i = 0; i < _vehicleColliderObjectCount; i++)
            {
                _vehicleColliderObjects[i].layer = _initColliderLayers[i];
            }
        }


        private void RegisterWithWheelControllerManager()
        {
            FindOrAddWheelControllerManager();
            _wheelControllerManager.Register(this);
        }


        private void DeregisterWithWheelControllerManager()
        {
            FindOrAddWheelControllerManager();
            _wheelControllerManager.Deregister(this);
        }


        private void FindOrAddWheelControllerManager()
        {
            if (_wheelControllerManager == null)
            {
                _wheelControllerManager = GetComponentInParent<WheelControllerManager>();
                if (_wheelControllerManager == null)
                {
                    _wheelControllerManager = targetRigidbody.gameObject.AddComponent<WheelControllerManager>();
                }
            }
        }


        private void DisableMotionVectors()
        {
            // Disable motion vectors as these can cause issues with PP when wheel is rotating
            if (disableMotionVectors)
            {
                MeshRenderer[] meshRenderers = wheel.visual.GetComponentsInChildren<MeshRenderer>();
                foreach (MeshRenderer mr in meshRenderers)
                {
                    mr.motionVectorGenerationMode = MotionVectorGenerationMode.ForceNoMotion;
                }
            }
        }


        private void Reset()
        {
            SetRuntimeDefaults();

            // Assume 4 as the component count might be wrong at this
            // point and wheels added at a later time.
            int wheelCount = 4;

            float gravity = -Physics.gravity.y;
            float weightPerWheel = targetRigidbody.mass * gravity / wheelCount;

            spring.maxForce = weightPerWheel * 6f;
            damper.bumpRate = weightPerWheel * 0.15f;
            damper.reboundRate = weightPerWheel * 0.15f;
            loadRating = weightPerWheel * 2f;
        }


        /// <summary>
        ///     Sets default values if they have not already been set.
        ///     Gets called each time Reset() is called in editor - such as adding the script to a GameObject.
        /// </summary>
        /// <param name="reset">Sets default values even if they have already been set.</param>
        /// <param name="findWheelVisuals">Should script attempt to find wheel visuals automatically by name and position?</param>
        public void SetRuntimeDefaults(bool reset = false, bool findWheelVisuals = true)
        {
            // Find parent Rigidbody
            if (targetRigidbody == null) targetRigidbody = gameObject.GetComponentInParent<Rigidbody>();
            Debug.Assert(targetRigidbody != null, "Parent does not contain a Rigidbody.");

            if (wheel == null || reset) wheel = new Wheel();
            if (spring == null || reset) spring = new Spring();
            if (damper == null || reset) damper = new Damper();
            if (forwardFriction == null || reset) forwardFriction = new Friction();
            if (sideFriction == null || reset) sideFriction = new Friction();
            if (activeFrictionPreset == null || reset)
                activeFrictionPreset = Resources.Load<FrictionPreset>("Wheel Controller 3D/Defaults/DefaultFrictionPreset");
            if (spring.forceCurve == null || spring.forceCurve.keys.Length == 0 || reset)
                spring.forceCurve = GenerateDefaultSpringCurve();
        }


        private AnimationCurve GenerateDefaultSpringCurve()
        {
            AnimationCurve ac = new AnimationCurve();
            ac.AddKey(0.0f, 0.0f);
            ac.AddKey(1.0f, 1.0f);
            return ac;
        }


        /// <summary>
        /// Places the WheelController roughly to the position it should be in, in relation to the wheel visual (if assigned).
        /// </summary>
        public void PositionToVisual()
        {
            if (wheel.visual == null)
            {
                Debug.LogError("Wheel visual not assigned.");
                return;
            }

            Rigidbody rb = GetComponentInParent<Rigidbody>();
            if (rb == null)
            {
                Debug.LogError("Rigidbody not found in parent.");
                return;
            }

            int wheelCount = GetComponentInParent<Rigidbody>().GetComponentsInChildren<WheelController>().Length;
            if (wheelCount == 0) return;

            // Approximate static load on the wheel.
            float approxStaticLoad = (rb.mass * -Physics.gravity.y) / wheelCount;

            // Approximate the spring travel, not taking spring curve into account.
            float approxSpringTravel = Mathf.Clamp01(approxStaticLoad / spring.maxForce) * spring.maxLength;

            // Position the WheelController transform above the wheel.
            transform.position = wheel.visual.transform.position + rb.transform.up * (spring.maxLength - approxSpringTravel);
        }

        private void ShowDtWarning()
        {
#if UNITY_EDITOR
            if (!SessionState.GetBool("WC3D_ShownDtWarning", false) && Time.fixedDeltaTime > 0.017f)
            {
                Debug.LogWarning($"Time.fixedDeltaTime of {Time.fixedDeltaTime} detected. Recommended value is 0.01 (100Hz) or lower for " +
                    $"best vehicle physics behaviour. On mobile games no higher than 0.02 (50Hz) is recommended. Higher physics update rate" +
                    $" results in higher physics fidelity.");
                SessionState.SetBool("WC3D_ShownDtWarning", true);
            }
#endif
        }
    }
}



#if UNITY_EDITOR
namespace NWH.WheelController3D
{
    /// <summary>
    ///     Editor for WheelController.
    /// </summary>
    [CustomEditor(typeof(WheelController))]
    [CanEditMultipleObjects]
    public class WheelControllerEditor : NUIEditor
    {
        public override bool OnInspectorNUI()
        {
            if (!base.OnInspectorNUI()) return false;

            WheelController wc = target as WheelController;
            if (wc == null) return false;

            float logoHeight = 40f;
            Rect texRect = drawer.positionRect;
            texRect.height = logoHeight;
            drawer.DrawEditorTexture(texRect, "Wheel Controller 3D/Editor/logo_wc3d", ScaleMode.ScaleToFit);
            drawer.Space(logoHeight + 4);


            int tabIndex = drawer.HorizontalToolbar("wc3dMenu",
                                     new[] { "Wheel", "Suspension", "Friction", "Misc", "Debug" }, true, true);

            if (tabIndex == 0) // WHEEL
            {
                drawer.BeginSubsection("Wheel");
                drawer.Field("targetRigidbody");
                drawer.Field("wheel.radius", true, "m");
                drawer.Field("wheel.width", true, "m");
                drawer.Field("wheel.mass", true, "kg");
                drawer.Field("loadRating", true, "N");
                drawer.Info("It is important to set the load rating correctly as it affects friction drastically.\r\n" +
                    "A value of about 2x of the Load at rest (Debug tab) is a good guidance.");
                drawer.Field("rollingResistanceTorque", true, "Nm");
                drawer.EndSubsection();

                drawer.BeginSubsection("Wheel Model");
                drawer.Field("wheel.visual");
                drawer.Field("wheel.nonRotatingVisual", true, "", "Non-Rotating Visual (opt.)");
                drawer.EndSubsection();
            }
            else if (tabIndex == 1) // SUSPENSION
            {
                drawer.BeginSubsection("Spring");
                drawer.Field("spring.maxForce", true, "N@100%");
                if (Application.isPlaying)
                    if (wc != null)
                    {
                        float minRecommended = wc.ParentRigidbody.mass * -Physics.gravity.y / 4f;
                        if (wc.SpringMaxForce < minRecommended)
                            drawer.Info(
                                "MaxForce of Spring is most likely too low for the vehicle mass. Minimum recommended for current configuration is" +
                                $" {minRecommended}N.", MessageType.Warning);
                    }

                if (drawer.Field("spring.maxLength", true, "m").floatValue < Time.fixedDeltaTime * 10f)
                    drawer.Info(
                        $"Minimum recommended spring length for Time.fixedDeltaTime of {Time.fixedDeltaTime} is {Time.fixedDeltaTime * 10f}");

                drawer.Field("spring.forceCurve");
                drawer.Info("X: Spring compression [%], Y: Force coefficient");
                drawer.EndSubsection();

                drawer.BeginSubsection("Damper");
                drawer.Field("damper.bumpRate", true, "Ns/m");
                drawer.Field("damper.slowBump", true, "slope");
                drawer.Field("damper.fastBump", true, "slope");
                drawer.Field("damper.bumpDivisionVelocity", true, "m/s");
                drawer.Space();
                drawer.Field("damper.reboundRate", true, "Ns/m");
                drawer.Field("damper.slowRebound", true, "slope");
                drawer.Field("damper.fastRebound", true, "slope");
                drawer.Field("damper.reboundDivisionVelocity", true, "m/s");
                drawer.EndSubsection();

                drawer.BeginSubsection("General");
                drawer.Field("suspensionExtensionSpeedCoeff");
                drawer.Field("forceApplicationPointDistance", true, null, "Force App. Point Distance");
                drawer.Field("antiSquat", true, "x100%");
                drawer.Field("camber", true, "deg");
                drawer.Info("For dynamic camber, use the CamberController component.");
                drawer.EndSubsection();
            }
            else if (tabIndex == 2) // FRICTION
            {
                drawer.BeginSubsection("Friction");
                drawer.Field("activeFrictionPreset");
                drawer.EmbeddedObjectEditor<NUIEditor>(((WheelController)target).FrictionPreset,
                                                       drawer.positionRect);

                drawer.BeginSubsection("Friction Circle");
                drawer.Field("frictionCircleStrength", true, null, "Strength");
                drawer.Field("frictionCircleShape", true, null, "Shape");
                drawer.EndSubsection();

                drawer.BeginSubsection("Longitudinal / Forward");
                drawer.Field("forwardFriction.stiffness", true, "x100 %");
                drawer.Field("forwardFriction.grip", true, "x100 %");
                drawer.EndSubsection();

                drawer.BeginSubsection("Lateral / Sideways");
                drawer.Field("sideFriction.stiffness", true, "x100 %");
                drawer.Field("sideFriction.grip", true, "x100 %");
                drawer.EndSubsection();
                drawer.EndSubsection();
            }
            else if (tabIndex == 3) // MISC
            {
                drawer.BeginSubsection("Actions");
                if (drawer.Button("Position To Visual"))
                {
                    foreach (WheelController targetWC in targets)
                    {
                        targetWC.PositionToVisual();
                    }
                }
                drawer.EndSubsection();


                drawer.BeginSubsection("Damage");
                {
                    drawer.Field("damageMaxWobbleAngle");
                }
                drawer.EndSubsection();


                drawer.BeginSubsection("Rendering");
                {
                    drawer.Field("disableMotionVectors");
                }
                drawer.EndSubsection();


                drawer.BeginSubsection("Layers");
                {
                    drawer.Field("layerMask");
                    drawer.Field("meshColliderLayer");
                }
                drawer.EndSubsection();



                drawer.BeginSubsection("Other");
                {
                    drawer.Field("otherBodyForceScale");
                }
                drawer.EndSubsection();
            }
            else
            {
                drawer.Label($"Is Grounded: {wc.IsGrounded}");
                drawer.Space();

                drawer.Label("Wheel");
                drawer.Label($"\tSteer Angle: {wc.SteerAngle}");
                drawer.Label($"\tMotor Torque: {wc.MotorTorque}");
                drawer.Label($"\tBrake Torque: {wc.BrakeTorque}");
                drawer.Label($"\tAng. Vel: {wc.AngularVelocity}");

                drawer.Label("Friction");
                drawer.Label($"\tLng. Slip: {wc.LongitudinalSlip}");
                drawer.Label($"\tLng. Speed: {wc.forwardFriction.speed}");
                drawer.Label($"\tLng. Force: {wc.forwardFriction.force}");
                drawer.Label($"\tLat. Slip: {wc.LateralSlip}");
                drawer.Label($"\tLat. Speed: {wc.sideFriction.speed}");
                drawer.Label($"\tLat. Force: {wc.sideFriction.force}");

                drawer.Label("Suspension");
                drawer.Label($"\tLoad: {wc.Load}");
                drawer.Label($"\tSpring Length: {wc.SpringLength}");
                drawer.Label($"\tSpring Force: {wc.spring.force}");
                drawer.Label($"\tSpring Velocity: {wc.spring.compressionVelocity}");
                drawer.Label($"\tSpring State: {wc.spring.extensionState}");
                drawer.Label($"\tDamper Force: {wc.damper.force}");
            }

            drawer.EndEditor(this);
            return true;
        }


        public override bool UseDefaultMargins()
        {
            return false;
        }
    }
}

#endif