import httpx
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from game_manager import active_games
import asyncio
import traceback

ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # Maps game_id -> { user_id: WebSocket instance }
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str, user_id: str):
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        self.active_connections[game_id][user_id] = websocket

    def disconnect(self, websocket: WebSocket, game_id: str, user_id: str):
        if (game_id in self.active_connections and
                user_id in self.active_connections[game_id]):

            # ONLY delete if the current active socket is the one disconnecting
            if self.active_connections[game_id][user_id] == websocket:
                del self.active_connections[game_id][user_id]

                # Clean up empty games to prevent memory leaks
                if not self.active_connections[game_id]:
                    del self.active_connections[game_id]

    async def send_personal_message(
        self, message: dict, game_id: str, user_id: str
    ):
        if (game_id in self.active_connections and
                user_id in self.active_connections[game_id]):
            ws = self.active_connections[game_id][user_id]
            await ws.send_json(message)

    async def broadcast_to_game(self, message: dict, game_id: str):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id].values():
                await connection.send_json(message)

    async def broadcast_game_state(self, game_id: str, game):
        """Broadcasts player-specific state to everyone in the room."""
        if game_id in self.active_connections:
            for uid, ws in self.active_connections[game_id].items():
                state = game.get_state_for_player(uid)
                await ws.send_json({"event": "game_state", "data": state})


# Initialize a global manager instance
manager = ConnectionManager()


async def request_replacement_bot(game_id: str):
    """Fires a background HTTP request to replace a dropped bot."""
    bot_url = os.environ.get(
        "BOT_SERVICE_URL", "http://bots:8001/api/spawn_bots")
    bot_secret = os.environ.get("BOT_SECRET", "default_dev_secret")

    async with httpx.AsyncClient() as client:
        try:
            await client.post(bot_url, json={
                "gameId": game_id,
                "botCount": 1,  # Request exactly one replacement
                "botSecret": bot_secret
            }, timeout=5.0)
            print(f"🔄 SOS sent: Requested 1 replacement bot for {game_id}")
        except Exception as e:
            print(
                f"⚠️ Failed to request replacement bot from Bot Service: {e}")


async def process_game_event(
    event: str, payload: dict, game_id: str, user_id: str, game
):
    """Handles specific game actions to reduce cyclomatic complexity."""
    if event == 'start_game_request':
        if game.host_id == user_id and game.start_game():
            await manager.broadcast_to_game(
                {"event": "game_started", "data": {"day": 1}}, game_id
            )
            await manager.broadcast_game_state(game_id, game)
    elif event == 'request_update':
        state = game.get_state_for_player(user_id)
        await manager.send_personal_message(
            {"event": "game_state", "data": state}, game_id, user_id
        )

    elif event == 'send_chat':

        new_message = game.handle_chat(user_id, payload)

        if new_message:

            message_dict = new_message.to_dict()
            print("New chat message:", message_dict)

            # GLOBAL CHAT
            if new_message.to_id == "GLOBAL":

                await manager.broadcast_to_game(
                    {
                        "event": "new_chat_message",
                        "data": message_dict
                    },
                    game_id
                )

            elif new_message.to_id in [chat.id for chat in game.chats]:  # GROUP CHAT

                await manager.broadcast_to_game(
                    {
                        "event": "new_chat_message",
                        "data": message_dict
                    },
                    game_id
                )

            # PRIVATE CHAT
            else:

                # sender
                await manager.send_personal_message(
                    {
                        "event": "new_chat_message",
                        "data": message_dict
                    },
                    game_id,
                    new_message.from_id
                )

                # recipient
                await manager.send_personal_message(
                    {
                        "event": "new_chat_message",
                        "data": message_dict
                    },
                    game_id,
                    new_message.to_id
                )

    elif event == 'submit_action':
        if game.status == "WAITING":
            return

        if game.handle_action(user_id, payload):
            await manager.broadcast_game_state(game_id, game)
        else:
            action_cmd = payload.get('action_command', payload.get('actionId'))
            await manager.send_personal_message({
                "event": "error",
                "data": {
                    "message": "Action rejected by game rules.",
                    "action_command": action_cmd
                }
            }, game_id, user_id)

    elif event == "create_chat":

        chat = game.create_chat(
            creator_id=user_id,
            name=payload["name"],
            member_ids=payload["memberIds"]
        )

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

                print("JOIN_ROOM RECEIVED")
                print("user_id =", user_id)
                print("game_id =", game_id)

                if not game:

                    await websocket.send_json({
                        "event": "error",
                        "data": {
                            "message": "Game not found."
                        }
                    })

                    continue

                game.add_player(user_id)

                await manager.connect(
                    websocket,
                    game_id,
                    user_id
                )

                print(
                    f"HOST CHECK: "
                    f"user={user_id} "
                    f"host={game.host_id} "
                    f"connected={game.host_connected}"
                )

                if game.host_id == user_id and not game.host_connected:
                    game.host_connected = True

                # INITIAL CHAT HISTORY
                # -----------------------------------

                await manager.send_personal_message(
                    {
                        "event": "chat_history",
                        "data": game.get_private_chat_history(user_id)
                    },
                    game_id,
                    user_id
                )

                # -----------------------------------
                # INITIAL GAME STATE
                # -----------------------------------

                await manager.send_personal_message(
                    {
                        "event": "game_state",
                        "data": game.get_state_for_player(user_id)
                    },
                    game_id,
                    user_id
                )

                # -----------------------------------
                # ROOM COUNT UPDATE
                # -----------------------------------

                await manager.broadcast_to_game(
                    {
                        "event": "room_update",
                        "data": {
                            "player_count": len(game.players)
                        }
                    },
                    game_id
                )

                print(f"✅ Player {user_id} joined game {game_id}")

                # -----------------------------------
                # HEADLESS AUTO-START TRIGGER
                # -----------------------------------
                if game.training and game.status == "RUNNING":
                    await manager.broadcast_to_game(
                        {"event": "game_started", "data": {"day": 1}}, game_id
                    )
                    await manager.broadcast_game_state(game_id, game)
                    print(f"🚀 Training Game {game_id} Auto-Started!")

            # ---------------------------------------
            # NORMAL GAME EVENTS
            # ---------------------------------------

            elif game_id and user_id:

                game = active_games.get(game_id)

                if not game:
                    continue

                await process_game_event(
                    event,
                    payload,
                    game_id,
                    user_id,
                    game
                )

    except WebSocketDisconnect:
        if game_id and user_id:
            manager.disconnect(websocket, game_id, user_id)
            print(f"Player {user_id} disconnected from {game_id}")

            game = active_games.get(game_id)

            # SELF-HEALING LOBBY LOGIC
            if game and game.status == "WAITING":
                game.remove_player(user_id)

                # If the disconnected user was a bot, request a replacement
                if user_id.startswith("bot_"):
                    asyncio.create_task(request_replacement_bot(game_id))

                # Broadcast the updated player count to the frontend
                asyncio.create_task(
                    manager.broadcast_to_game(
                        {
                            "event": "room_update",
                            "data": {
                                "player_count": len(game.players)
                            }
                        },
                        game_id
                    )
                )
        else:
            print("Unregistered socket disconnected before joining a room.")

    except Exception:
        traceback.print_exc()

        # Only attempt to disconnect if the user successfully joined a room
        if game_id and user_id:
            manager.disconnect(websocket, game_id, user_id)
