import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import api  # noqa: E402


def test_spawn_bots_fails_closed_with_wrong_configured_secret(monkeypatch):
    monkeypatch.setattr(api, "get_bot_config", lambda: {"secret": "configured-secret"})
    monkeypatch.setattr(
        api, "spawn_bot_processes",
        lambda **_kwargs: pytest.fail("unauthenticated request spawned bots"),
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(api.spawn_bots(api.SpawnBotsRequest(
            gameId="game-1",
            botCount=1,
            botSecret="default_dev_secret",
            botModel="GOAPGenetic",
        )))

    assert exc.value.status_code == 403


def test_spawn_bots_requires_matching_configured_secret(monkeypatch):
    spawned = []
    monkeypatch.setattr(api, "get_bot_config", lambda: {"secret": "test-secret"})
    monkeypatch.setattr(
        api, "spawn_bot_processes",
        lambda **kwargs: spawned.append(kwargs),
    )

    response = asyncio.run(api.spawn_bots(api.SpawnBotsRequest(
        gameId="game-1",
        botCount=1,
        botSecret="test-secret",
        botModel="GOAPGenetic",
    )))

    assert response["status"] == "success"
    assert spawned[0]["game_id"] == "game-1"
