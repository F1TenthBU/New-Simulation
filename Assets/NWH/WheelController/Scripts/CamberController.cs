using UnityEngine;

#if UNITY_EDITOR
using UnityEditor;
using NWH.NUI;
#endif

namespace NWH.WheelController3D
{
    /// <summary>
    /// Applies camber to the WheelController based on spring compression.
    /// </summary>
    [RequireComponent(typeof(WheelController))]
    public class CamberController : MonoBehaviour
    {
        /// <summary>
        /// Curve representing spring compression on X-axis and 
        /// camber angle on Y-axis.
        /// </summary>
        [UnityEngine.Tooltip("Curve representing spring compression on X-axis and \r\ncamber angle on Y-axis.")]
        public AnimationCurve camberCurve;

        private WheelController _wc;

        private void Awake()
        {
            _wc = GetComponent<WheelController>();
        }

        private void FixedUpdate()
        {
            _wc.Camber = camberCurve.Evaluate(_wc.SpringCompression);
        }
    }
}


#if UNITY_EDITOR
namespace NWH.WheelController3D
{
    /// <summary>
    ///     Editor for WheelController.
    /// </summary>
    [CustomEditor(typeof(CamberController))]
    [CanEditMultipleObjects]
    public class CamberControllerEditor : NUIEditor
    {
        public override bool OnInspectorNUI()
        {
            if (!base.OnInspectorNUI()) return false;

            drawer.Field("camberCurve");

            drawer.Info("X: Spring Compression | Y: Camber Angle");

            drawer.EndEditor(this);
            return true;
        }
    }
}
#endif