from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.dependencies import ws_manager

router = APIRouter()


@router.websocket("/ws/incidents/{incident_id}")
async def incident_ws(websocket: WebSocket, incident_id: str) -> None:
    await ws_manager.connect(incident_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(incident_id, websocket)
