import asyncio
import hmac
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from service.api.websocket.game_events import process_game_event


AUTHENTICATION_ERROR = {
    "event": "error",
    "data": {"message": "WebSocket authentication failed."},
}


def _join_error(websocket, message):
    return websocket.send_json({"event": "error", "data": {"message": message}})


def _is_authenticated(websocket, payload, game, database):
    user_id = payload.get("userId")
    if not isinstance(user_id, str) or not user_id:
        return False
    if user_id.startswith("bot_"):
        supplied_secret = payload.get("botSecret", "")
        expected_secret = os.environ.get("BOT_SECRET")
        return (
            bool(expected_secret)
            and isinstance(supplied_secret, str)
            and hmac.compare_digest(supplied_secret, expected_secret or "")
            and user_id in game.players
        )
    session_id = websocket.cookies.get("user_session")
    return (
        session_id == user_id
        and database.user_exists(user_id)
    )


def create_router(registry, manager, database, bot_client=None):
    router = APIRouter()

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        user_id = game_id = None
        try:
            while True:
                packet = await websocket.receive_json()
                if not isinstance(packet, dict):
                    await _join_error(websocket, "Invalid WebSocket packet.")
                    continue
                event, payload = packet.get("event"), packet.get("data", {})
                if not isinstance(event, str) or not isinstance(payload, dict):
                    await _join_error(websocket, "Malformed WebSocket packet.")
                    continue

                if (user_id is not None
                        and manager.active_connections.get(
                            game_id, {}).get(user_id) is not websocket):
                    await _join_error(websocket, "WebSocket connection was replaced.")
                    await websocket.close(code=4001)
                    return

                if event == "join_room":
                    if user_id is not None:
                        await _join_error(websocket, "WebSocket is already joined to a game.")
                        continue
                    candidate_user_id = payload.get("userId")
                    candidate_game_id = payload.get("gameId")
                    game = registry.get(candidate_game_id)
                    if not game:
                        await _join_error(websocket, "Game not found.")
                        continue
                    if not _is_authenticated(websocket, payload, game, database):
                        await websocket.send_json(AUTHENTICATION_ERROR)
                        continue
                    if (game.status != "WAITING"
                            and candidate_user_id not in game.players):
                        await _join_error(
                            websocket, "Player is not a member of this game.")
                        continue
                    user_id, game_id = candidate_user_id, candidate_game_id
                    game.add_player(user_id)
                    await manager.connect(websocket, game_id, user_id)
                    if game.host_id == user_id and not game.host_connected:
                        game.host_connected = True
                        await manager.broadcast_game_state(game_id, game)
                    await manager.send_personal_message(
                        {"event": "chat_history",
                         "data": game.get_private_chat_history(user_id)}, game_id, user_id)
                    await manager.send_game_state(game_id, game, user_id)
                    await manager.broadcast_to_game(
                        {"event": "room_update", "data": {"player_count": len(game.players)}},
                        game_id)
                    if game.training and game.status == "RUNNING":
                        await manager.broadcast_to_game(
                            {"event": "game_started", "data": {"day": 1}}, game_id)
                        await manager.broadcast_game_state(game_id, game)
                elif game_id and user_id:
                    game = registry.get(game_id)
                    if game:
                        await process_game_event(
                            event, payload, game_id, user_id, game, manager)
        except WebSocketDisconnect:
            if game_id and user_id:
                disconnected = manager.disconnect(websocket, game_id, user_id)
                game = registry.get(game_id)
                if disconnected and game and game.status == "WAITING":
                    game.remove_player(user_id)
                    if user_id.startswith("bot_") and bot_client:
                        asyncio.create_task(bot_client.spawn_bots(
                            game_id, 1, None, "genetic", timeout=5.0))
                    asyncio.create_task(manager.broadcast_to_game(
                        {"event": "room_update",
                         "data": {"player_count": len(game.players)}}, game_id))
        except Exception:
            if game_id and user_id:
                manager.disconnect(websocket, game_id, user_id)

    return router
