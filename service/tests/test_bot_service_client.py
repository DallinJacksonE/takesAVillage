import importlib
import os
import sys
import types
import unittest

SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

httpx_stub = types.ModuleType("httpx")
setattr(httpx_stub, "AsyncClient", object)
sys.modules["httpx"] = httpx_stub

bot_service_client = importlib.import_module("bot_service_client")


class BotServiceClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_spawn_bots_returns_typed_success_result(self):
        requests = []

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def post(self, url, json, timeout):
                requests.append((url, json, timeout))

        client = bot_service_client.BotServiceClient(
            base_url="http://bots:8001",
            bot_secret="secret",
            client_factory=FakeClient,
        )

        result = await client.spawn_bots(
            game_id="game-1",
            bot_count=3,
            base_genome=[{"food_weight": 1.0}],
            bot_model="GOAPGenetic",
            training_attempt_index=2,
        )

        self.assertTrue(result.ok)
        self.assertIsNone(result.error_message)
        self.assertEqual(requests[0][0], "http://bots:8001/api/spawn_bots")
        self.assertEqual(requests[0][1]["trainingAttemptIndex"], 2)

    async def test_fetch_game_genomes_retries_all_endpoint_before_fallback(self):
        calls = []

        class FakeResponse:
            def __init__(self, status_code, payload=None, text=""):
                self.status_code = status_code
                self._payload = payload or {}
                self.text = text

            def json(self):
                return self._payload

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def get(self, url, timeout):
                calls.append(url)
                if url.endswith("/all") and len([call for call in calls if call.endswith("/all")]) < 2:
                    return FakeResponse(404, text="not ready")
                if url.endswith("/all"):
                    return FakeResponse(200, {"entries": [{"fitness": 12, "genome": {"food_weight": 1.0}}]})
                return FakeResponse(500, text="fallback should not be used")

        client = bot_service_client.BotServiceClient(
            base_url="http://bots:8001",
            bot_secret="secret",
            client_factory=FakeClient,
            retry_sleep_seconds=0,
        )

        result = await client.fetch_game_genomes("game-1", max_attempts=2)

        self.assertTrue(result.ok)
        self.assertEqual(result.entries, [{"fitness": 12, "genome": {"food_weight": 1.0}}])
        self.assertEqual(calls, [
            "http://bots:8001/api/genomes/game-1/all",
            "http://bots:8001/api/genomes/game-1/all",
        ])


if __name__ == "__main__":
    unittest.main()
