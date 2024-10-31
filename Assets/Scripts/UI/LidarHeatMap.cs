using UnityEngine;
using UnityEngine.UI;

public class LidarHeatMap : MonoBehaviour
{
    public RawImage heatMapImage;
    public Texture2D heatMapTexture;

    private void Start()
    {
        // Initialize the heat map texture
        heatMapTexture = new Texture2D(150, 150);
        heatMapImage.texture = heatMapTexture;
    }
}