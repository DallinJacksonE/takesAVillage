import unittest

from service.game_manager import bot_client as bot_service_client


class BotServiceClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_models_returns_bot_service_models(self):
        class FakeResponse:
            status_code = 200

            @staticmethod
            def json():
                return {"models": ["genetic", "GOAPGenetic"]}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def get(self, url, timeout):
                self.request = (url, timeout)
                return FakeResponse()

        client = bot_service_client.BotServiceClient(
            "http://bots:8001", "secret", FakeClient)

        self.assertEqual(
            await client.fetch_models(), ["genetic", "GOAPGenetic"])

    async def test_spawn_bots_returns_typed_success_result(self):
        requests = []

        class FakeResponse:
            status_code = 200
            text = "ok"

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def post(self, url, json, timeout):
                requests.append((url, json, timeout))
                return FakeResponse()

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

    async def test_spawn_bots_reports_non_success_response(self):
        class FakeResponse:
            status_code = 403
            text = "forbidden"

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def post(self, _url, json, timeout):
                return FakeResponse()

        client = bot_service_client.BotServiceClient(
            "http://bots:8001", "wrong-secret", FakeClient)

        result = await client.spawn_bots(
            "game-1", 1, "random", "GOAPGenetic")

        self.assertFalse(result.ok)
        self.assertEqual(result.error_message, "forbidden")

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

    async def test_fetch_game_genomes_waits_for_expected_terminal_reports(self):
        all_requests = 0

        class FakeResponse:
            status_code = 200
            text = ""

            def __init__(self, entries):
                self.entries = entries

            def json(self):
                return {"entries": self.entries}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def get(self, _url, timeout):
                nonlocal all_requests
                all_requests += 1
                entries = [{"fitness": 12, "genome": {"food_weight": 1.0}}]
                if all_requests > 1:
                    entries.append({"fitness": 9, "genome": {"food_weight": 0.5}})
                return FakeResponse(entries)

        client = bot_service_client.BotServiceClient(
            base_url="http://bots:8001",
            bot_secret="secret",
            client_factory=FakeClient,
            retry_sleep_seconds=0,
        )

        result = await client.fetch_game_genomes(
            "game-1", expected_entry_count=2, max_attempts=2)

        self.assertTrue(result.ok)
        self.assertIsNotNone(result.entries)
        entries = result.entries or []
        self.assertEqual(len(entries), 2)
        self.assertEqual(all_requests, 2)


if __name__ == "__main__":
    unittest.main()
