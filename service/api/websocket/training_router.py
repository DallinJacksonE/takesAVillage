from fastapi import APIRouter, WebSocket, WebSocketDisconnect


def create_router(training_service, update_hub):
    router = APIRouter()

    @router.websocket("/ws/research/training-sessions")
    async def training_sessions(websocket: WebSocket):
        await update_hub.connect(websocket)
        await websocket.send_json({
            "event": "training_sessions",
            "data": training_service.list(),
        })
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            update_hub.disconnect(websocket)
        except Exception:
            update_hub.disconnect(websocket)

    return router
