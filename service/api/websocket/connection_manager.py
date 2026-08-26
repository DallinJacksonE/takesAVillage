import asyncio

from service.logging import BackendLogger


class ConnectionManager:
    def __init__(self, registry, logger=None):
        self.registry = registry
        self.logger = logger or BackendLogger("ws")
        self.active_connections = {}

    async def connect(self, websocket, game_id, user_id):
        connections = self.active_connections.setdefault(game_id, {})
        previous = connections.get(user_id)
        connections[user_id] = websocket
        if previous is not None and previous is not websocket:
            try:
                await previous.close(code=4001)
            except Exception:
                self.logger.warning(
                    f"Could not close replaced websocket for {user_id}")

    def has_connections(self, game_id):
        return bool(self.active_connections.get(game_id))

    async def disconnect_game(self, game_id, code=1000):
        """Close and remove every websocket owned by a game."""
        connections = self.active_connections.pop(game_id, {})
        if not connections:
            return 0

        closed = 0
        for websocket in list(connections.values()):
            try:
                await websocket.close(code=code)
                closed += 1
            except Exception:
                self.logger.warning(f"Could not close websocket for game {game_id}")
        return closed

    def disconnect(self, websocket, game_id, user_id):
        connections = self.active_connections.get(game_id)
        if not connections:
            return False
        if connections.get(user_id) is not websocket:
            return False
        connections.pop(user_id, None)
        if not connections:
            self.active_connections.pop(game_id, None)
        return True

    async def send_personal_message(self, message, game_id, user_id):
        connection = self.active_connections.get(game_id, {}).get(user_id)
        if not connection:
            return
        try:
            await connection.send_json(message)
        except Exception:
            self.disconnect(connection, game_id, user_id)

    async def _send(self, connection, message, user_id, failed):
        try:
            await connection.send_json(message)
        except Exception:
            failed.append((user_id, connection))

    async def broadcast_to_game(self, message, game_id):
        connections = self.active_connections.get(game_id, {})
        failed = []
        await asyncio.gather(*[
            self._send(connection, message, user_id, failed)
            for user_id, connection in list(connections.items())
        ])
        self._remove_failed(game_id, failed)

    async def broadcast_game_state(self, game_id, game):
        connections = self.active_connections.get(game_id, {})
        failed = []
        await asyncio.gather(*[
            self._send(connection,
                       {"event": "game_state", "data": game.get_state_for_player(user_id)},
                       user_id, failed)
            for user_id, connection in list(connections.items())
        ])
        self._remove_failed(game_id, failed)

    def _remove_failed(self, game_id, failed_connections):
        connections = self.active_connections.get(game_id, {})
        game = self.registry.get(game_id)
        for user_id, failed_connection in failed_connections:
            if connections.get(user_id) is not failed_connection:
                continue
            connections.pop(user_id, None)
            if game and game.status == "WAITING":
                game.remove_player(user_id)
        if not connections:
            self.active_connections.pop(game_id, None)
