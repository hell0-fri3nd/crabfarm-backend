from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services import WebSockets as WebSocketsManager
import json

WebSockets = APIRouter(prefix="/ws/v1/websockets", tags=["Web Sockets"])

SocketManager = WebSocketsManager()

@WebSockets.websocket("/sensors")
async def websocket_endpoint(websocket: WebSocket):
    await SocketManager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            # device = payload["device"]
            # weight = payload["weight"]

            # print(f"Device: {device}  Weight: {weight}")
            # 🔥 broadcast to all clients (React will receive)
            await SocketManager.broadcast(json.dumps(payload))

    except WebSocketDisconnect:
        SocketManager.disconnect(websocket)