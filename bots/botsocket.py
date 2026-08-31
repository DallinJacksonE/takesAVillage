import asyncio
import json
import httpx
import websockets
from websockets.exceptions import ConnectionClosed
from typing import Callable, Awaitable, Optional
from logger import Logger  # <-- Import type hint


class BotSocket:
    def __init__(
        self,
        game_id: str,
        bot_secret: str,
        logger: Logger,  # <-- Require logger dependency
        http_url: str = "http://localhost:5000",
        ws_url: str = "ws://localhost:5000/ws",
        decision_interval: float = 0.1,
    ):
        self.game_id = game_id
        self.bot_secret = bot_secret
        self.logger = logger
        self.http_url = http_url
        self.ws_url = ws_url

        self.user_id = None
        self.websocket = None
        self._listen_task = None
        self._decision_task = None
        self._latest_game_state = None
        self._latest_state_revision = -1
        self._state_available = asyncio.Event()
        self.decision_interval = decision_interval

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
            self.websocket is not None
            and self._listen_task
            and not self._listen_task.done()
        ):
            return True

        if not self.user_id:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"{self.http_url}/api/botJoinGame",
                        json={"gameId": self.game_id,
                              "botSecret": self.bot_secret}
                    )
                    if response.status_code != 200:
                        self.logger.stdout_error(f"Failed to join game "
                                                 f"{self.game_id}: {response.text}")
                        return False

                    data = response.json()
                    self.user_id = data["userId"]
                    self.logger.info(
                        f"Authenticated with Game Server. ID: {self.user_id}")
                except Exception as e:
                    self.logger.stdout_error(
                        "HTTP API request failed", exception=e)
                    return False

        try:
            self.logger.info(f"Connecting bot "
                             f"{self.user_id} to WebSocket {self.ws_url}")
            self.websocket = await websockets.connect(
                self.ws_url, ping_interval=20, ping_timeout=20,
                close_timeout=10, max_size=None
            )

            await self._send("join_room", {
                "userId": self.user_id,
                "gameId": self.game_id,
                "botSecret": self.bot_secret,
            })

            self._listen_task = asyncio.create_task(self._listen_loop())
            self.logger.info(
                f"WebSocket successfully connected for bot {self.user_id}")
            return True

        except Exception as e:
            self.logger.stdout_error(f"WebSocket connection failed for bot "
                                     f"{self.user_id}", exception=e)
            return False

    async def disconnect(self):
        if self.websocket:
            try:
                await self.websocket.close()
                self.logger.info("WebSocket disconnected gracefully.")
            except Exception as e:
                self.logger.handled_error(
                    "Error closing websocket", exception=e)
            finally:
                self.websocket = None
        current_task = asyncio.current_task()
        tasks = []
        for task_name in ("_listen_task", "_decision_task"):
            task = getattr(self, task_name)
            if task:
                task.cancel()
                if task is not current_task:
                    tasks.append(task)
            setattr(self, task_name, None)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _queue_game_state(self, state):
        revision = state.get("state_revision", -1)
        if revision < self._latest_state_revision:
            return
        self._latest_state_revision = max(
            self._latest_state_revision, revision)
        self._latest_game_state = state
        self._state_available.set()
        if not self._decision_task or self._decision_task.done():
            self._decision_task = asyncio.create_task(
                self._process_game_states())

    async def _process_game_states(self):
        try:
            while True:
                try:
                    await asyncio.wait_for(
                        self._state_available.wait(),
                        timeout=self.decision_interval,
                    )
                except asyncio.TimeoutError:
                    pass
                self._state_available.clear()
                state = self._latest_game_state
                if state is not None and self.on_game_state:
                    await self.on_game_state(state)
        except asyncio.CancelledError:
            pass
        finally:
            if asyncio.current_task() is self._decision_task:
                self._decision_task = None

    async def _listen_loop(self):
        try:
            async for message in self.websocket:
                packet = json.loads(message)
                event = packet.get("event")
                data = packet.get("data")

                if event == "game_state" and self.on_game_state:
                    if data.get("status") == "WAITING":
                        continue
                    self._queue_game_state(data)
                elif event == "chat_history" and self.on_chat_history:
                    await self.on_chat_history(data)
                elif event == "new_chat_message" and self.on_new_chat_message:
                    await self.on_new_chat_message(data)
                elif event == "game_started" and self.on_game_started:
                    await self.on_game_started(data)
                elif event == "error" and self.on_error:
                    self.logger.handled_error(
                        f"Server sent error event: {data}")
                    await self.on_error(data)

        except ConnectionClosed:
            self.logger.info(f"Bot {self.user_id} disconnected from server.")
        except Exception as e:
            self.logger.stdout_error(
                "Unexpected error in websocket listen loop", exception=e)
        finally:
            self.websocket = None
            self._listen_task = None
            decision_task = self._decision_task
            if decision_task and decision_task is not asyncio.current_task():
                decision_task.cancel()
                await asyncio.gather(decision_task, return_exceptions=True)
                self._decision_task = None
            if self.on_disconnect:
                await self.on_disconnect()

    async def _send(self, event: str, payload: dict):
        if self.websocket:
            packet = json.dumps({"event": event, "data": payload})
            try:
                await self.websocket.send(packet)
            except Exception as e:
                self.logger.stdout_error(f"Failed to send packet "
                                         f"{event}", exception=e)
                self.logger.info(f"Packet payload: {packet}")

    # Outgoing events remain the same...
    async def request_update(self):
        await self._send("request_update", {})

    async def send_chat(self, content: str, to_id: str = "GLOBAL"):
        await self._send("send_chat",
                         {"content": content, "to_id": to_id})

    async def submit_action(self, payload: dict):
        await self._send("submit_action", payload)

    async def create_chat(self, name: str, member_ids: list[str]):
        await self._send("create_chat",
                         {"name": name, "memberIds": member_ids})
