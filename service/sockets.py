import httpx
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from game_manager import active_games
import asyncio
from logger import BackendLogger

ws_router = APIRouter()
ws_logger = BackendLogger("ws")


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str, user_id: str):
        if game_id not in self.active_connections.keys():
            self.active_connections[game_id] = {}
        self.active_connections[game_id][user_id] = websocket

    def disconnect(self, websocket: WebSocket, game_id: str, user_id: str):
        try:
            if game_id in self.active_connections:
                self.active_connections[game_id].pop(user_id, None)
                if not self.active_connections[game_id]:
                    del self.active_connections[game_id]
        except Exception as e:
            ws_logger.error(f"Error during disconnect for "
                            f"user={user_id}", exc=e)

    async def send_personal_message(self, message: dict, game_id: str, user_id: str):
        try:
            ws = self.active_connections[game_id][user_id]
            await ws.send_json(message)
        except Exception as e:
            ws_logger.error(
                f"Failed to send personal message game={game_id} user={user_id}", exc=e
            )
            self.active_connections.get(game_id, {}).pop(user_id, None)

    async def _send_safe(self, connection, message: dict, game_id: str, user_id: str, dead_users: list[str]):
        try:
            await connection.send_json(message)
        except Exception as e:
            ws_logger.error(
                f"Safe send failed for game={game_id} user={user_id}", exc=e
            )
            dead_users.append(user_id)

    async def broadcast_to_game(self, message: dict, game_id: str):
        if game_id not in self.active_connections:
            return

        dead_users: list[str] = []
        tasks = []

        for user_id, connection in list(self.active_connections[game_id].items()):
            tasks.append(
                self._send_safe(connection, message,
                                game_id, user_id, dead_users)
            )

        if tasks:
            await asyncio.gather(*tasks)

        for user_id in dead_users:
            self.active_connections[game_id].pop(user_id, None)
            game = active_games.get(game_id)
            if game:
                game.remove_player(user_id)
                ws_logger.info(f"Removed disconnected player "
                               f"{user_id} from game {game_id}")

    async def broadcast_game_state(self, game_id: str, game):
        if game_id not in self.active_connections:
            return

        dead_users: list[str] = []
        tasks = []

        for user_id, ws in list(self.active_connections[game_id].items()):
            state = game.get_state_for_player(user_id)
            tasks.append(
                self._send_safe(
                    ws, {"event": "game_state", "data": state}, game_id, user_id, dead_users)
            )

        if tasks:
            await asyncio.gather(*tasks)

        for user_id in dead_users:
            self.active_connections[game_id].pop(user_id, None)
            game = active_games.get(game_id)
            if game:
                game.remove_player(user_id)
                ws_logger.info(f"Removed disconnected player "
                               f"{user_id} from game {game_id}")


manager = ConnectionManager()


async def request_replacement_bot(game_id: str):
    bot_url = os.environ.get(
        "BOT_SERVICE_URL", "http://bots:8001/api/spawn_bots")
    bot_secret = os.environ.get("BOT_SECRET", "default_dev_secret")

    async with httpx.AsyncClient() as client:
        try:
            await client.post(bot_url, json={
                "gameId": game_id,
                "botCount": 1,
                "botSecret": bot_secret
            }, timeout=5.0)
            ws_logger.info(
                f"SOS sent: Requested 1 replacement bot for {game_id}")
        except Exception as e:
            ws_logger.error(
                "Failed to request replacement bot from Bot Service", exc=e)


async def process_game_event(event: str, payload: dict, game_id: str, user_id: str, game):
    if event == 'start_game_request':
        if game.host_id == user_id and game.start_game():
            await manager.broadcast_to_game({"event": "game_started", "data": {"day": 1}}, game_id)
            await manager.broadcast_game_state(game_id, game)
    elif event == 'request_update':
        state = game.get_state_for_player(user_id)
        await manager.send_personal_message({"event": "game_state", "data": state}, game_id, user_id)

    elif event == 'send_chat':
        new_message = game.handle_chat(user_id, payload)
        if new_message:
            message_dict = new_message.to_dict()
            if new_message.to_id == "GLOBAL" or new_message.to_id in [chat.id for chat in game.chats]:
                await manager.broadcast_to_game({"event": "new_chat_message", "data": message_dict}, game_id)
            else:
                await manager.send_personal_message({"event": "new_chat_message", "data": message_dict}, game_id, new_message.from_id)
                await manager.send_personal_message({"event": "new_chat_message", "data": message_dict}, game_id, new_message.to_id)

    elif event == 'submit_action':
        if game.status == "WAITING":
            return

        if game.handle_action(user_id, payload):
            await manager.broadcast_game_state(game_id, game)
        else:
            action_cmd = payload.get('action_command', payload.get('actionId'))
            await manager.send_personal_message({
                "event": "error",
                "data": {"message": "Action rejected by game rules.", "action_command": action_cmd}
            }, game_id, user_id)

    elif event == "create_chat":
        chat = game.create_chat(user_id, payload["name"], payload["memberIds"])
        if chat:
            await manager.broadcast_game_state(game_id, game)


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    user_id = None
    game_id = None

    try:
        while True:
            packet = await websocket.receive_json()
            event = packet.get("event")
            payload = packet.get("data", {})

            if event == "join_room":
                user_id = payload.get("userId")
                game_id = payload.get("gameId")
                game = active_games.get(game_id)

                if not game:
                    await websocket.send_json({
                        "event": "error",
                        "data": {"message": "Game not found."}
                    })
                    continue

                game.add_player(user_id)
                await manager.connect(websocket, game_id, user_id)

                if game.host_id == user_id and not game.host_connected:
                    game.host_connected = True
                    await manager.broadcast_game_state(game_id, game)

                await manager.send_personal_message(
                    {"event": "chat_history", "data": game.get_private_chat_history(
                        user_id)}, game_id, user_id
                )
                await manager.send_personal_message(
                    {"event": "game_state", "data": game.get_state_for_player(
                        user_id)}, game_id, user_id
                )
                await manager.broadcast_to_game(
                    {"event": "room_update", "data": {
                        "player_count": len(game.players)}}, game_id
                )

                ws_logger.info(f"Player {user_id} joined game {game_id}")

                if game.training and game.status == "RUNNING":
                    await manager.broadcast_to_game({"event": "game_started", "data": {"day": 1}}, game_id)
                    await manager.broadcast_game_state(game_id, game)
                    ws_logger.info(f"Training Game {game_id} Auto-Started!")

            elif game_id and user_id:
                game = active_games.get(game_id)
                if not game:
                    continue
                await process_game_event(event, payload, game_id, user_id, game)

    except WebSocketDisconnect:
        if game_id and user_id:
            manager.disconnect(websocket, game_id, user_id)
            ws_logger.info(f"Player {user_id} disconnected from {game_id}")

            game = active_games.get(game_id)
            if game and game.status == "WAITING":
                game.remove_player(user_id)

                if user_id.startswith("bot_"):
                    asyncio.create_task(request_replacement_bot(game_id))

                asyncio.create_task(manager.broadcast_to_game(
                    {"event": "room_update", "data": {
                        "player_count": len(game.players)}}, game_id
                ))
        else:
            ws_logger.warning(
                "Unregistered socket disconnected before joining a room.")

    except Exception:
        ws_logger.exception("Unexpected exception in WebSocket endpoint")
        if game_id and user_id:
            manager.disconnect(websocket, game_id, user_id)
