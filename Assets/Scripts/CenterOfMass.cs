using UnityEngine;

/// <summary>
/// Sets the center of mass of an object.
/// </summary>
public class CenterOfMass : MonoBehaviour
{
    /// <summary>
    /// Center of mass, set in Unity editor.
    /// </summary>
    [SerializeField]
    private Vector3 Com = Vector3.zero;

    public float gizmoSize = 0.2f;

    private Rigidbody body;

    void Start()
    {
        body = this.GetComponent<Rigidbody>();
    }
    void Update()
    {
        if (body != null)
            body.centerOfMass = this.Com;
    }
    
    private void OnDrawGizmosSelected()
    {
        Gizmos.matrix = transform.localToWorldMatrix;

        if (gizmoSize > 0)
        {
            Gizmos.color = Color.yellow;
            Gizmos.DrawSphere(Com, gizmoSize);
        }
    }
}
