using UnityEngine;
using NativeWebSocket;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;

public class WebSocketClient : MonoBehaviour
{
    private WebSocket websocket;
    private Racecar racecar;

    private Drive drive;

    async void Start()
    {
        racecar = GetComponent<Racecar>();
        drive = GetComponent<Drive>();

        websocket = new WebSocket("ws://localhost:8765");

        websocket.OnOpen += () =>
        {
            Debug.Log("Connection open!");
        };

        websocket.OnError += (e) =>
        {
            Debug.Log("Error! " + e);
        };

        websocket.OnClose += (e) =>
        {
            Debug.Log("Connection closed!");
        };

        websocket.OnMessage += (bytes) =>
        {
            var message = Encoding.UTF8.GetString(bytes);
            Debug.Log("Message received: " + message);
            var command = JsonUtility.FromJson<CommandData>(message);
            if (command.command == "update")
            {
                racecar.Drive.Speed = (float)command.speed;
                racecar.Drive.Angle = (float)command.angle;
                Debug.Log($"Updated car: speed={command.speed}, angle={command.angle}");
            }
        };

        await websocket.Connect();
    }

    void Update()
    {
        #if !UNITY_WEBGL || UNITY_EDITOR
            websocket.DispatchMessageQueue();
        #endif
    }

    private async void OnApplicationQuit()
    {
        await websocket.Close();
    }
}