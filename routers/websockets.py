from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from database import SessionLocal
from services import WebSockets as WebSocketsManager
from models import SensorLogs
from sqlalchemy import select
from datetime import datetime, timedelta 
from sqlalchemy.orm import Session

import json

WebSockets = APIRouter(prefix="/ws/v1/websockets", tags=["Web Sockets"])

SocketManager = WebSocketsManager()

SENSOR_THRESHOLDS = {
    "do": {
        "warning": [
            [4.5, 4.9],
            [12.1, 12.5]
        ],
        "danger": [
            [0, 4.5],
            [12.5, float("inf")]
        ]
    },

    "temperature": {
        "warning": [
            [24.1, 24.5],
            [35.1, 35.5]
        ],
        "danger": [
            [float("-inf"), 24.1],
            [35.5, float("inf")]
        ]
    },

    "ph": {
        "warning": [
            [7.1, 7.4],
            [9.1, 9.5]
        ],
        "danger": [
            [float("-inf"), 7.1],
            [9.5, float("inf")]
        ]
    },

    "tds": {
        "warning": [
            [14.5, 14.9],
            [20.1, 20.5]
        ],
        "danger": [
            [float("-inf"), 14.5],
            [20.5, float("inf")]
        ]
    },

    "ammonium": {
        "warning": [
            [0.1, 0.4],
            [3.1, 3.5]
        ],
        "danger": [
            [float("-inf"), 0.1],
            [3.5, float("inf")]
        ]
    }
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_status(sensor_type, value):

    thresholds = SENSOR_THRESHOLDS.get(sensor_type)

    if not thresholds:
        return "NORMAL"

    # Check DANGER first
    for min_val, max_val in thresholds["danger"]:
        if min_val <= value <= max_val:
            return "DANGER"

    # Check WARNING
    for min_val, max_val in thresholds["warning"]:
        if min_val <= value <= max_val:
            return "WARNING"

    return "NORMAL"

def insert_sensor_log(db, sensor_type, value):

    # Do not insert if no data
    if value is None:
        return False
    
    current_hour = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    query = select(SensorLogs).where(
        SensorLogs.sensor_type == sensor_type,
        SensorLogs.created_at >= current_hour
    )
    existing = db.execute(query).scalars().first()
    
    if existing:
        return False
    
    new_log = SensorLogs(
        sensor_type=sensor_type,
        status=get_status(sensor_type, value),
        value=value
    )

    db.add(new_log)
    db.commit()

    return True

@WebSockets.websocket("/sensors")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
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

            insert_sensor_log(db,"temperature", payload.get("temperature"))
            insert_sensor_log(db,"ph", payload.get("ph"))
            insert_sensor_log(db,"tds", payload.get("tds"))
            insert_sensor_log(db,"turbidity", payload.get("turbidity"))
            insert_sensor_log(db,"ammonium", payload.get("ammonium"))
            insert_sensor_log(db,"do", payload.get("do"))

    except WebSocketDisconnect:
        SocketManager.disconnect(websocket)
        
        
        # def sensor_logs(data):
#     device = data.get("device")
#     temperature = data.get("temperature")
#     ph = data.get("ph")
#     tds = data.get("tds")
#     turbidity = data.get("turbidity")
#     ammonium = data.get("ammonium")
#     do = data.get("do")

    # {"device": "water_sensor", "temperature": 20.6, "ph": 7.1, "tds": 292.0, "turbidity": 4.4, "ammonium": 3.8, "do": 7.4}
    
    # if device == "water_sensor":
    #     print(f"Device: {device}")
    #     print(f"Temperature: {temperature}")
