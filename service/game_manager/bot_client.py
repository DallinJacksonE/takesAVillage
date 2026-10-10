import asyncio
from dataclasses import dataclass
from typing import Any, Callable

import httpx


@dataclass(frozen=True)
class BotServiceResult:
    ok: bool
    error_message: str | None = None
    entries: list[dict[str, Any]] | None = None


class BotServiceClient:
    def __init__(self, base_url: str, bot_secret: str,
                 client_factory: Callable[..., Any] | None = None,
                 retry_sleep_seconds: float = 0.1):
        self.base_url = base_url.rstrip("/")
        self.bot_secret = bot_secret
        self.client_factory = client_factory or httpx.AsyncClient
        self.retry_sleep_seconds = retry_sleep_seconds

    async def fetch_models(self, timeout: float = 3.0) -> list[str]:
        try:
            async with self.client_factory() as client:
                response = await client.get(
                    f"{self.base_url}/api/models", timeout=timeout)
                if response.status_code == 200:
                    return response.json().get("models", []) or []
        except Exception:
            pass
        return []

    async def spawn_bots(self, game_id: str, bot_count: int, base_genome: Any,
                         bot_model: str, training_attempt_index: int | None = None,
                         timeout: float = 10.0) -> BotServiceResult:
        payload = {"gameId": game_id, "botCount": bot_count,
                   "botSecret": self.bot_secret, "baseGenome": base_genome,
                   "botModel": bot_model}
        if training_attempt_index is not None:
            payload["trainingAttemptIndex"] = training_attempt_index
        try:
            async with self.client_factory() as client:
                response = await client.post(
                    f"{self.base_url}/api/spawn_bots", json=payload,
                    timeout=timeout)
            if response.status_code != 200:
                return BotServiceResult(
                    ok=False,
                    error_message=getattr(
                        response, "text", "Bot service rejected spawn request"),
                )
            return BotServiceResult(ok=True)
        except Exception as exc:
            return BotServiceResult(ok=False, error_message=str(exc))

    async def cancel_bots(self, game_id: str, timeout: float = 5.0) -> BotServiceResult:
        try:
            async with self.client_factory() as client:
                response = await client.post(
                    f"{self.base_url}/api/cancel_bots/{game_id}",
                    json={"botSecret": self.bot_secret},
                    timeout=timeout,
                )
            if response.status_code != 200:
                return BotServiceResult(
                    ok=False,
                    error_message=getattr(response, "text", "Bot service rejected cancellation"),
                )
            return BotServiceResult(ok=True)
        except Exception as exc:
            return BotServiceResult(ok=False, error_message=str(exc))

    async def fetch_game_genomes(self, game_id: str, max_attempts: int = 3,
                                 timeout: float = 10.0,
                                 expected_entry_count: int = 1) -> BotServiceResult:
        expected_entry_count = max(1, expected_entry_count)
        async with self.client_factory() as client:
            last_error = None
            latest_entries = []
            for attempt in range(max(1, max_attempts)):
                try:
                    response = await client.get(
                        f"{self.base_url}/api/genomes/{game_id}/all", timeout=timeout)
                    if response.status_code == 200:
                        entries = response.json().get("entries", []) or []
                        if entries:
                            latest_entries = entries
                            if len(entries) >= expected_entry_count:
                                return BotServiceResult(ok=True, entries=entries)
                            last_error = (
                                f"Received {len(entries)}/{expected_entry_count} "
                                "genome entries"
                            )
                        else:
                            last_error = "Genome endpoint returned no entries"
                    else:
                        last_error = getattr(response, "text", "genome entries unavailable")
                except Exception as exc:
                    last_error = str(exc)
                if attempt < max_attempts - 1:
                    await asyncio.sleep(self.retry_sleep_seconds)
            # Do not discard reports that arrived just because one or more bots
            # disconnected before submitting terminal fitness.
            if latest_entries:
                return BotServiceResult(ok=True, entries=latest_entries)
            try:
                response = await client.get(
                    f"{self.base_url}/api/genomes/{game_id}", timeout=timeout)
                if response.status_code == 200:
                    data = response.json()
                    genome = data.get("genome")
                    if genome:
                        return BotServiceResult(ok=True, entries=[{
                            "game_id": game_id,
                            "fitness": data.get("best_fitness", 0),
                            "genome": genome,
                        }])
                    return BotServiceResult(ok=True, entries=[])
                last_error = getattr(response, "text", last_error)
            except Exception as exc:
                last_error = str(exc)
        return BotServiceResult(ok=False,
                                error_message=last_error or "No genome entries returned",
                                entries=[])
