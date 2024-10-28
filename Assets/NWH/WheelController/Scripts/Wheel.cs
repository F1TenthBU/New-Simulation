using System;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.Serialization;

namespace NWH.WheelController3D
{
    /// <summary>
    ///     Contains everything wheel related, including rim and tire.
    /// </summary>
    [Serializable]
    public class Wheel
    {
        /// <summary>
        ///     GameObject representing the visual aspect of the wheel / wheel mesh.
        ///     Should not have any physics colliders attached to it.
        /// </summary>
        [Tooltip(
            "GameObject representing the visual aspect of the wheel / wheel mesh.\r\nShould not have any physics colliders attached to it.")]
        public GameObject visual;

        /// <summary>
        /// Chached value for visual.transform to avoid overhead.
        /// Visual should have been a Transform from the start, but for backwards-compatibility it was left as a GameObject.
        /// </summary>
        [UnityEngine.Tooltip("Chached value for visual.transform to avoid overhead.\r\nVisual should have been a Transform from the start, but for backwards-compatibility it was left as a GameObject.")]
        public Transform visualTransform;

        /// <summary>
        /// Object containing the wheel MeshColliders.
        /// </summary>
        [UnityEngine.Tooltip("Object containing the wheel MeshColliders.")]
        public GameObject colliderGO;

        /// <summary>
        /// Cached value of colliderGO.transform.
        /// </summary>
        [UnityEngine.Tooltip("Cached value of colliderGO.transform.")]
        public Transform colliderTransform;

        /// <summary>
        /// Collider covering the top half of the wheel. 
        /// </summary>
        [UnityEngine.Tooltip("Collider covering the top half of the wheel. ")]
        public MeshCollider topMeshCollider;

        /// <summary>
        /// Collider covering the bottom half of the wheel. 
        /// Active only is cases of side collision, bottoming out and native friction.
        /// </summary>
        [UnityEngine.Tooltip("Collider covering the bottom half of the wheel. \r\nActive only is cases of side collision, bottoming out and native friction.")]
        public MeshCollider bottomMeshCollider;

        /// <summary>
        /// ID of the bottom collider.
        /// </summary>
        [UnityEngine.Tooltip("ID of the bottom collider.")]
        public int bottomMeshColliderID;

        /// <summary>
        /// ID of the top collider.
        /// </summary>
        [UnityEngine.Tooltip("ID of the top collider.")]
        public int topMeshColliderID;

        /// <summary>
        ///     Object representing non-rotating part of the wheel. This could be things such as brake calipers, external fenders,
        ///     etc.
        /// </summary>
        [Tooltip(
            "Object representing non-rotating part of the wheel. This could be things such as brake calipers, external fenders, etc.")]
        public GameObject nonRotatingVisual;

        /// <summary>
        ///     Current angular velocity of the wheel in rad/s.
        /// </summary>
        [Tooltip("    Current angular velocity of the wheel in rad/s.")]
        public float angularVelocity;

        /// <summary>
        ///     Current wheel RPM.
        /// </summary>
        public float rpm
        {
            get { return angularVelocity * 9.55f; }
        }

        /// <summary>
        ///     Forward vector of the wheel in world coordinates.
        /// </summary>
        [Tooltip("    Forward vector of the wheel in world coordinates.")]
        [NonSerialized]
        public Vector3 forward;

        /// <summary>
        ///     Vector in world coordinates pointing to the right of the wheel.
        /// </summary>
        [Tooltip("    Vector in world coordinates pointing to the right of the wheel.")]
        [NonSerialized]
        public Vector3 right;

        /// <summary>
        ///     Wheel's up vector in world coordinates.
        /// </summary>
        [Tooltip("    Wheel's up vector in world coordinates.")]
        [NonSerialized]
        public Vector3 up;

        /// <summary>
        /// Total inertia of the wheel and any attached components.
        /// </summary>
        public float inertia;

        /// <summary>
        /// Inertia of the wheel, without any attached components.
        /// </summary>
        public float baseInertia;

        /// <summary>
        ///     Mass of the wheel. Inertia is calculated from this.
        /// </summary>
        [Tooltip("    Mass of the wheel. Inertia is calculated from this.")]
        public float mass = 20.0f;

        /// <summary>
        ///     Position offset of the non-rotating part.
        /// </summary>
        [Tooltip("    Position offset of the non-rotating part.")]
        [NonSerialized]
        public Vector3 nonRotatingVisualPositionOffset;

        /// <summary>
        ///     Rotation offset of the non-rotating part.
        /// </summary>
        [Tooltip("    Rotation offset of the non-rotating part.")]
        [NonSerialized]
        public Quaternion nonRotatingVisualRotationOffset;

        /// <summary>
        ///     Total radius of the tire in [m].
        /// </summary>
        [Tooltip("    Total radius of the tire in [m].")]
        [Min(0.001f)]
        public float radius = 0.35f;

        /// <summary>
        ///     Current rotation angle of the wheel visual in regards to it's X axis vector.
        /// </summary>
        [Tooltip("    Current rotation angle of the wheel visual in regards to it's X axis vector.")]
        [NonSerialized]
        public float axleAngle;

        /// <summary>
        ///     Width of the tyre.
        /// </summary>
        [Tooltip("    Width of the tyre.")]
        [Min(0.001f)]
        public float width = 0.25f;

        /// <summary>
        ///     Position of the wheel in world coordinates.
        /// </summary>
        [Tooltip("    Position of the wheel in world coordinates.")]
        [NonSerialized]
        public Vector3 worldPosition; // TODO

        /// <summary>
        ///     Position of the wheel in the previous physics update in world coordinates.
        /// </summary>
        [NonSerialized]
        [UnityEngine.Tooltip("    Position of the wheel in the previous physics update in world coordinates.")]
        public Vector3 prevWorldPosition;

        /// <summary>
        ///     Position of the wheel relative to the WheelController transform.
        /// </summary>
        [NonSerialized]
        [UnityEngine.Tooltip("    Position of the wheel relative to the WheelController transform.")]
        public Vector3 localPosition;

        /// <summary>
        ///     Angular velocity during the previus FixedUpdate().
        /// </summary>
        [NonSerialized]
        [UnityEngine.Tooltip("    Angular velocity during the previus FixedUpdate().")]
        public float prevAngularVelocity;

        /// <summary>
        ///     Rotation of the wheel in world coordinates.
        /// </summary>
        [Tooltip("    Rotation of the wheel in world coordinates.")]
        [NonSerialized]
        public Quaternion worldRotation;

        /// <summary>
        /// Local rotation of the wheel.
        /// </summary>
        [NonSerialized] public Quaternion localRotation;

        /// <summary>
        /// Width of the wheel during the previous frame.
        /// </summary>
        [NonSerialized] public float prevWidth;

        /// <summary>
        /// Radius of the wheel during the previous frame.
        /// </summary>
        [NonSerialized] public float prevRadius;


        /// <summary>
        /// Called when either radius or width of the wheel change.
        /// </summary>
        [NonSerialized]
        [UnityEngine.Tooltip("Called when either radius or width of the wheel change.")]
        public UnityEvent onWheelDimensionsChange = new UnityEvent();


        public void Initialize(in WheelController wc)
        {
            Transform controllerTransform = wc.transform;

            // Create an empty wheel visual if not assigned
            if (visual == null)
            {
                visual = CreateEmptyVisual(controllerTransform, wc.spring.maxLength);
            }
            visualTransform = visual.transform;

            // v2.0 or newer requires the wheel visual to be parented directly to the WheelController.
            if (visualTransform.parent != controllerTransform)
            {
                visualTransform.SetParent(controllerTransform);
            }

            SetupMeshColliders(controllerTransform, wc.meshColliderLayer);

            // Initialize wheel vectors
            Transform cachedVisualTransform = visual.transform;
            worldPosition = cachedVisualTransform.position;
            localPosition = controllerTransform.InverseTransformPoint(worldPosition);
            localPosition.x = 0;
            localPosition.z = 0;
            worldPosition = controllerTransform.TransformPoint(localPosition);
            up = cachedVisualTransform.up;
            forward = cachedVisualTransform.forward;
            right = cachedVisualTransform.right;

            // Initialize non-rotating visual
            if (nonRotatingVisual != null)
            {
                nonRotatingVisualPositionOffset =
                    visual.transform.InverseTransformPoint(nonRotatingVisual.transform.position);
                nonRotatingVisualRotationOffset = (Quaternion.Inverse(wc.transform.rotation)
                                                  * nonRotatingVisual.transform.rotation);
            }

            UpdatePhysicalProperties();
        }


        private void SetupMeshColliders(in Transform parent, int meshColliderLayer)
        {
            // Check for any existing colliders on the visual and remove them
            Collider[] visualColliders = visual.GetComponentsInChildren<Collider>();
            if (visualColliders.Length > 0)
            {
                for (int i = visualColliders.Length - 1; i >= 0; i--)
                {
                    GameObject.Destroy(visualColliders[i]);
                }
            }

            // Add wheel mesh collider
            colliderGO = new GameObject()
            {
                name = "MeshCollider"
            };
            colliderTransform = colliderGO.transform;
            colliderTransform.position = visualTransform.position;
            colliderTransform.SetParent(parent);

            topMeshCollider = colliderGO.AddComponent<MeshCollider>();
            topMeshCollider.convex = true;
            topMeshCollider.gameObject.layer = meshColliderLayer; // Ignore self raycast hit.
            topMeshCollider.material.bounceCombine = PhysicMaterialCombine.Minimum;
            topMeshCollider.material.frictionCombine = PhysicMaterialCombine.Minimum;
            topMeshCollider.material.bounciness = 0;
            topMeshCollider.material.staticFriction = 0;
            topMeshCollider.material.dynamicFriction = 0;

            bottomMeshCollider = colliderGO.AddComponent<MeshCollider>();
            bottomMeshCollider.convex = true;
            bottomMeshCollider.gameObject.layer = meshColliderLayer; // Ignore self raycast hit.
            bottomMeshCollider.material.bounceCombine = PhysicMaterialCombine.Minimum;
            bottomMeshCollider.material.frictionCombine = PhysicMaterialCombine.Minimum;
            bottomMeshCollider.material.bounciness = 0;
            bottomMeshCollider.material.staticFriction = 0;
            bottomMeshCollider.material.dynamicFriction = 0;
        }


        public void CheckForWheelDimensionChange()
        {
            // Check for radius change
            if (prevRadius != radius || prevWidth != width)
            {
                UpdatePhysicalProperties();
            }
            prevRadius = radius;
            prevWidth = width;
        }


        /// <summary>
        /// Used to update the wheel parameters (inertia, scale, etc.) after one of the wheel 
        /// dimensions is changed.
        /// </summary>
        public void UpdatePhysicalProperties()
        {
            inertia = 0.5f * mass * radius * radius;
            baseInertia = inertia;

            // Collider be null when setting up outside of play mode, so do a check.
            if (bottomMeshCollider != null)
            {
                // Undersize the bottom collider slightly so that it does not lose contact with the ground as easily
                // when spring length is 0 and so that it does not push the vehicle away once it is enabled, if near an obstacle.
                float radiusUndersizing = Mathf.Clamp(radius * 0.05f, 0, 0.025f);
                float widthUndersizing = Mathf.Clamp(width * 0.05f, 0, 0.025f);
                bottomMeshCollider.sharedMesh = WheelControllerUtility.CreateWheelMesh(
                    radius - radiusUndersizing,
                    width - widthUndersizing, false);
            }

            if (topMeshCollider != null)
            {
                // Oversize the top collider slightly so that it prevents the unwanted ground detection from the sides and front.
                float oversizing = Mathf.Clamp(radius * 0.1f, 0, 0.1f);
                topMeshCollider.sharedMesh = WheelControllerUtility.CreateWheelMesh(
                    radius + oversizing,
                    width + oversizing, true);
            }
        }


        private GameObject CreateEmptyVisual(in Transform parentTransform, in float springMaxLength)
        {
            GameObject visual = new GameObject($"{parentTransform.name}_emptyVisual");
            visual.transform.parent = parentTransform;
            visual.transform.SetPositionAndRotation(parentTransform.position - parentTransform.up * (springMaxLength * 0.5f),
                parentTransform.rotation);
            return visual;
        }
    }
}