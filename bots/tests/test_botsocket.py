import asyncio
import json

from botsocket import BotSocket


class LoggerStub:
    def info(self, *_args, **_kwargs):
        pass

    def handled_error(self, *_args, **_kwargs):
        pass

    def stdout_error(self, *_args, **_kwargs):
        pass


class FakeWebSocket:
    def __init__(self):
        self.messages = asyncio.Queue()

    def __aiter__(self):
        return self

    async def __anext__(self):
        message = await self.messages.get()
        if message is None:
            raise StopAsyncIteration
        return message

    async def close(self):
        await self.messages.put(None)


async def wait_until(predicate, timeout=0.5):
    async def poll():
        while not predicate():
            await asyncio.sleep(0)

    await asyncio.wait_for(poll(), timeout=timeout)


def test_socket_keeps_receiving_while_game_state_decision_is_running():
    async def scenario():
        socket = BotSocket("game-1", "secret", LoggerStub())
        websocket = FakeWebSocket()
        socket.websocket = websocket
        first_started = asyncio.Event()
        release_first = asyncio.Event()
        handled = []

        async def on_game_state(state):
            handled.append(state["state_revision"])
            if state["state_revision"] == 1:
                first_started.set()
                await release_first.wait()

        socket.on_game_state = on_game_state
        listener = asyncio.create_task(socket._listen_loop())
        await websocket.messages.put(json.dumps({
            "event": "game_state",
            "data": {"status": "RUNNING", "state_revision": 1},
        }))
        await first_started.wait()
        await websocket.messages.put(json.dumps({
            "event": "game_state",
            "data": {"status": "RUNNING", "state_revision": 2},
        }))

        await wait_until(
            lambda: socket._latest_game_state["state_revision"] == 2
        )
        assert handled == [1]

        release_first.set()
        await wait_until(lambda: 2 in handled)
        await websocket.close()
        await listener
        await socket.disconnect()

    asyncio.run(scenario())


def test_bot_decision_loop_wakes_without_another_websocket_packet():
    async def scenario():
        socket = BotSocket(
            "game-1", "secret", LoggerStub(), decision_interval=0.01
        )
        calls = []
        called_twice = asyncio.Event()

        async def on_game_state(state):
            calls.append(state["state_revision"])
            if len(calls) >= 2:
                called_twice.set()

        socket.on_game_state = on_game_state
        socket._latest_game_state = {
            "status": "RUNNING",
            "state_revision": 4,
        }
        socket._state_available.set()
        socket._decision_task = asyncio.create_task(
            socket._process_game_states()
        )

        await asyncio.wait_for(called_twice.wait(), timeout=0.2)
        assert calls[:2] == [4, 4]
        await socket.disconnect()

    asyncio.run(scenario())
