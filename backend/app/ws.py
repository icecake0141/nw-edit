"""WebSocket handlers for real-time job updates."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

from .job_manager import job_manager


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(websocket)

        # Register callback with job manager
        async def callback(message: dict):
            await self.send_message(job_id, message)

        job_manager.register_ws_callback(job_id, callback)

    async def disconnect(self, job_id: str, websocket: WebSocket):
        """Disconnect and unregister a WebSocket connection."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_message(self, job_id: str, message: dict):
        """Send a message to all connections for a job."""
        if job_id not in self.active_connections:
            return

        # Make a copy to avoid modification during iteration
        connections = self.active_connections[job_id].copy()

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection failed, remove it
                self.active_connections[job_id].discard(connection)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for job updates."""
    await manager.connect(job_id, websocket)

    try:
        # Keep connection alive and receive any client messages
        while True:
            _ = await websocket.receive_text()
            # Echo or ignore client messages (not used in this implementation)
    except WebSocketDisconnect:
        await manager.disconnect(job_id, websocket)
    except Exception:
        await manager.disconnect(job_id, websocket)
