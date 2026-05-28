from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from game_manager import active_games

ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # Maps game_id -> { user_id: WebSocket instance }
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str, user_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        self.active_connections[game_id][user_id] = websocket

    def disconnect(self, game_id: str, user_id: str):
        if (game_id in self.active_connections and
                user_id in self.active_connections[game_id]):
            del self.active_connections[game_id][user_id]
            # Clean up empty games to prevent memory leaks
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

    async def send_personal_message(self, message: dict,
                                    game_id: str, user_id: str):
        if (game_id in self.active_connections and
                user_id in self.active_connections[game_id]):
            ws = self.active_connections[game_id][user_id]
            await ws.send_json(message)

    async def broadcast_to_game(self, message: dict, game_id: str):
        if game_id in self.active_connections:
            for ws in self.active_connections[game_id].values():
                await ws.send_json(message)

    async def broadcast_game_state(self, game):
        """Helper to send individualized states to all players in a game."""
        if game.id in self.active_connections:
            for pid, ws in self.active_connections[game.id].items():
                state = game.get_state_for_player(pid)
                await ws.send_json({"event": "game_state", "data": state})


manager = ConnectionManager()


@ws_router.websocket("/ws/{game_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, user_id: str):

    # 1. PURGE: Remove the player from any other active games
    for g_id, g in list(active_games.items()):
        if g_id != game_id and user_id in g.players:
            del g.players[user_id]
            if len(g.players) == 0:
                del active_games[g_id]

    if game_id not in active_games:
        await websocket.accept()
        await websocket.send_json(
            {"event": "error", "data": {"message": "Game not found."}})
        await websocket.close()
        return

    game = active_games[game_id]

    # 2. REJOIN SAFEGUARD: Only add them if they aren't already in the game
    if user_id not in game.players:
        if game.status != "WAITING":
            await websocket.accept()
            await websocket.send_json(
                {"event": "error", "data":
                 {"message": "Cannot join. Game in progress."}})
            await websocket.close()
            return
        game.add_player(user_id)

    # 3. Add to Connection Manager
    await manager.connect(websocket, game_id, user_id)

    # Send room update and initial state
    await manager.broadcast_to_game(
        {"event": "room_update", "data":
         {"player_count": len(game.players)}}, game_id)
    await manager.send_personal_message(
        {"event": "game_state", "data":
         game.get_state_for_player(user_id)}, game_id, user_id)

    try:
        # Core Listening Loop
        while True:
            packet = await websocket.receive_json()
            event = packet.get("event")
            payload = packet.get("data", {})

            if event == 'start_game_request':
                if game.host_id == user_id and game.start_game():
                    await manager.broadcast_to_game(
                        {"event": "game_started", "data": {"day": 1}}, game_id)

            elif event == 'request_update':
                await manager.send_personal_message(
                    {"event": "game_state", "data":
                     game.get_state_for_player(user_id)}, game_id, user_id)

            elif event == 'send_chat':
                if game.handle_chat(user_id, payload):
                    await manager.broadcast_game_state(game)

            elif event == 'submit_action':
                if game.handle_action(user_id, payload):
                    await manager.broadcast_game_state(game)
                else:
                    action_cmd = payload.get(
                        'action_command') or payload.get('actionId')
                    await manager.send_personal_message({
                        "event": "error",
                        "data": {"message":
                                 "Action rejected by game rules.",
                                 "action_command": action_cmd}
                    }, game_id, user_id)

    except WebSocketDisconnect:
        manager.disconnect(game_id, user_id)
