import asyncio
import json
import httpx
import websockets
from typing import Callable, Awaitable, Optional


class BotSocket:
    def __init__(
        self,
        game_id: str,
        bot_secret: str,
        http_url: str = "http://localhost:5000",
        ws_url: str = "ws://localhost:5000/ws"
    ):
        self.game_id = game_id
        self.bot_secret = bot_secret
        self.http_url = http_url
        self.ws_url = ws_url

        self.user_id = None
        self.websocket = None
        self._listen_task = None

        # Callbacks for the bot logic to hook into
        self.on_game_state: Optional[Callable[[dict], Awaitable[None]]] = None
        self.on_chat_history: Optional[Callable[[
            list], Awaitable[None]]] = None
        self.on_new_chat_message: Optional[Callable[[
            dict], Awaitable[None]]] = None
        self.on_game_started: Optional[Callable[[
            dict], Awaitable[None]]] = None
        self.on_error: Optional[Callable[[dict], Awaitable[None]]] = None
        self.on_disconnect: Optional[Callable[[], Awaitable[None]]] = None

    async def connect(self):
        """Authenticates via HTTP (first connect) then opens the WebSocket."""
        # 1. Join Game via HTTP only on first connect

        if (
            self.websocket
            and not self.websocket.closed
            and self._listen_task
            and not self._listen_task.done()
        ):
            return True

        if not self.user_id:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.http_url}/api/botJoinGame",
                    json={
                        "gameId": self.game_id,
                        "botSecret": self.bot_secret
                    }
                )

                if response.status_code != 200:
                    print(f"Failed to join game {self.game_id}: {response.text}")
                    return False

                data = response.json()
                self.user_id = data["userId"]
                print(f"Bot authenticated with ID: {self.user_id}")

        # 2. Establish WebSocket Connection
        try:
            print(f"Connecting bot {self.user_id} to WebSocket {self.ws_url}")
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
                max_size=None
            )

            # 3. Send the join_room handshake
            await self._send("join_room", {
                "userId": self.user_id,
                "gameId": self.game_id
            })

            # 4. Start the background listening loop
            self._listen_task = asyncio.create_task(self._listen_loop())
            print(f"WebSocket connected for bot {self.user_id}")
            return True

        except Exception as e:
            print(f"WebSocket connection failed for bot {self.user_id} at {self.ws_url}: {e}")
            return False

    async def disconnect(self):
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
            finally:
                self.websocket = None
        if self._listen_task:
            self._listen_task.cancel()
            self._listen_task = None

    # ---------------------------------------
    # INTERNAL EVENT LOOP
    # ---------------------------------------

    async def _listen_loop(self):
        """Continuously reads incoming messages and triggers callbacks."""
        try:
            async for message in self.websocket:
                packet = json.loads(message)
                event = packet.get("event")
                data = packet.get("data")

                if event == "game_state" and self.on_game_state:
                    if data.get("status") == "WAITING":
                        continue
                    await self.on_game_state(data)

                elif event == "chat_history" and self.on_chat_history:
                    await self.on_chat_history(data)
                elif event == "new_chat_message" and self.on_new_chat_message:
                    await self.on_new_chat_message(data)
                elif event == "game_started" and self.on_game_started:
                    await self.on_game_started(data)
                elif event == "error" and self.on_error:
                    await self.on_error(data)

        except websockets.exceptions.ConnectionClosed:
            print(f"Bot {self.user_id} disconnected from server.")
            if self.on_disconnect:
                await self.on_disconnect()

    async def _send(self, event: str, payload: dict):
        """Helper to format and send JSON packets."""
        if self.websocket:
            packet = json.dumps({"event": event, "data": payload})
            try:
                await self.websocket.send(packet)
            except Exception as e:
                print(f"Failed to send packet '{event}' for bot {self.user_id}: {e}")
                print(f"Packet payload: {packet}")

    # ---------------------------------------
    # OUTGOING EVENTS (Called by Bot Logic)
    # ---------------------------------------

    async def request_update(self):
        await self._send("request_update", {})

    async def send_chat(self, content: str, to_id: str = "GLOBAL"):
        await self._send("send_chat", {
            "content": content,
            "to_id": to_id
        })

    async def submit_action(self, payload: dict):
        await self._send("submit_action", payload)

    async def create_chat(self, name: str, member_ids: list[str]):
        await self._send("create_chat", {
            "name": name,
            "memberIds": member_ids
        })
