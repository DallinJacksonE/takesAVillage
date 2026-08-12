import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from botsocket import BotSocket  # noqa: E402


class StubLogger:
    def info(self, *_args, **_kwargs):
        pass

    def handled_error(self, *_args, **_kwargs):
        pass

    def stdout_error(self, *_args, **_kwargs):
        pass


class RecordingWebSocket:
    def __init__(self):
        self.messages = []

    async def send(self, packet):
        self.messages.append(json.loads(packet))


def test_outbound_packets_match_shared_wire_fixtures():
    fixture_path = Path(__file__).resolve().parents[2] / "shared" / "fixtures" / "bot-wire.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    socket = BotSocket(
        game_id="game-1",
        bot_secret="test-secret",
        logger=StubLogger(),
        http_url="http://service:5000",
        ws_url="ws://service:5000/ws",
    )
    socket.user_id = "bot_1"
    socket.websocket = RecordingWebSocket()

    asyncio.run(socket.request_update())
    asyncio.run(socket.send_chat("hello"))
    asyncio.run(socket.submit_action({
        "action_command": "FINISH_PHASE",
        "payload": {},
    }))

    assert socket.websocket.messages == fixture["outboundWebSocketPackets"]
