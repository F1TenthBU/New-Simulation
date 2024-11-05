using UnityEngine;
using System.Collections;
using System.Net;
using System.Text;
using System.IO;
using System;

public class HTTPServer : MonoBehaviour
{
    private HttpListener listener;
    private Racecar racecar;

    void Start()
    {
        racecar = GetComponent<Racecar>();
        listener = new HttpListener();
        listener.Prefixes.Add("http://localhost:5000/");
        listener.Start();
        listener.BeginGetContext(new AsyncCallback(OnRequest), listener);
        Debug.Log("HTTP Server started on http://localhost:5000/");
    }

    void OnRequest(IAsyncResult result)
    {
        var context = listener.EndGetContext(result);
        var request = context.Request;
        var response = context.Response;

        Debug.Log($"Received request: {request.HttpMethod} {request.Url.AbsolutePath}");

        if (request.Url.AbsolutePath == "/lidar/samples" && request.HttpMethod == "GET")
        {
            Debug.Log("Handling GET /lidar/samples");
            var samples = racecar.Lidar.Samples;
            Debug.Log("  Got the samples");
            var json = JsonUtility.ToJson(samples);
            Debug.Log($"JSON response size" + json.Length);
            byte[] buffer = Encoding.UTF8.GetBytes(json);
            response.ContentLength64 = buffer.Length;
            Debug.Log("Size of response: " + buffer.Length);
            response.OutputStream.Write(buffer, 0, buffer.Length);
            response.StatusCode = (int)HttpStatusCode.OK;
            response.OutputStream.Flush();  // Ensure the data is sent
            response.OutputStream.Close();  // Ensure the stream is closed
            Debug.Log("Response for GET /lidar/samples sent");
        }
        else if (request.Url.AbsolutePath == "/car/control" && request.HttpMethod == "POST")
        {
            Debug.Log("Handling POST /car/control");
            using (var reader = new StreamReader(request.InputStream, request.ContentEncoding))
            {
                var json = reader.ReadToEnd();
                var controlData = JsonUtility.FromJson<ControlData>(json);
                racecar.Drive.Speed = controlData.speed;
                racecar.Drive.Angle = controlData.angle;
                Debug.Log($"Set car speed to {controlData.speed} and angle to {controlData.angle}");
            }
            response.StatusCode = (int)HttpStatusCode.OK;
            response.OutputStream.Close();  // Ensure the stream is closed
            Debug.Log("Response for POST /car/control sent");
        }
        else
        {
            response.StatusCode = (int)HttpStatusCode.NotFound;
            response.OutputStream.Close();  // Ensure the stream is closed
            Debug.Log("Response for unknown request sent");
        }

        listener.BeginGetContext(new AsyncCallback(OnRequest), listener);
    }

    void OnDestroy()
    {
        listener.Stop();
        Debug.Log("HTTP Server stopped.");
    }

    [System.Serializable]
    public class ControlData
    {
        public float speed;
        public float angle;
    }
}