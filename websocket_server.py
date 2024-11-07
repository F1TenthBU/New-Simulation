import asyncio
import websockets
import json

class CarControlServer:
    def __init__(self):
        self.speed = 0.0
        self.angle = 0.0
        self.sensor_data = {}

    async def handler(self, websocket, path):
        while True:
            # Example command to update car speed and angle
            command = {
                "command": "update",
                "speed": 1,  # Example speed value
                "angle": 0.9   # Example angle value
            }
            await websocket.send(json.dumps(command))
            print(f"Sent command: {command}")

            # Wait for a short period before sending the next command
            await asyncio.sleep(1)

            # Optionally, receive sensor data from Unity
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1)
                data = json.loads(message)
                if 'sensor_data' in data:
                    self.sensor_data = data['sensor_data']
                    print(f"Received sensor data: {self.sensor_data}")
            except asyncio.TimeoutError:
                pass

    async def main(self):
        async with websockets.serve(self.handler, "localhost", 8765):
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    server = CarControlServer()
    asyncio.run(server.main())