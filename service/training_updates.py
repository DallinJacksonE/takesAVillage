from fastapi import WebSocket
from logger import BackendLogger
from training_session_presenter import build_training_session_payload

updates_logger = BackendLogger("training_updates")


class TrainingUpdateHub:
    def __init__(self):
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self._connections.discard(websocket)

    async def send_current_state(self, websocket: WebSocket,
                                 active_training_sessions: dict):
        await websocket.send_json({
            "event": "training_sessions",
            "data": build_training_session_payload(active_training_sessions)
        })

    async def broadcast_sessions(self, active_training_sessions: dict):
        if not self._connections:
            return

        message = {
            "event": "training_sessions",
            "data": build_training_session_payload(active_training_sessions)
        }
        disconnected = []

        for websocket in list(self._connections):
            try:
                await websocket.send_json(message)
            except Exception as e:
                updates_logger.error(
                    "Failed to broadcast training session update", exc=e)
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)


training_update_hub = TrainingUpdateHub()
