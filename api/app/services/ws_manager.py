from fastapi import WebSocket

from app.schemas.ws import WSEvent


class ConnectionManager:
    """In-memory WebSocket connection manager. One list of connections per incident."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, incident_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(incident_id, []).append(websocket)

    def disconnect(self, incident_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(incident_id, [])
        if websocket in conns:
            conns.remove(websocket)

    async def broadcast(self, incident_id: str, event: WSEvent) -> None:
        for ws in self._connections.get(incident_id, []):
            await ws.send_text(event.model_dump_json())
