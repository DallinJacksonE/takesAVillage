import asyncio

import pytest

from service.db.memory import InMemoryDB
from service.game_manager.bot_client import BotServiceResult
from service.game_manager.lifecycle import GameLifecycleService
from service.game_manager.registry import GameRegistry
from service.research.training.service import TrainingConfig, TrainingService
from service.research.training.session_store import TrainingSessionStore


def test_session_store_does_not_expose_mutable_dictionary():
    store = TrainingSessionStore()
    session = {"generation": 1}
    store.add("session-1", session)

    listed = store.list()
    listed["session-1"]["generation"] = 99

    assert store.get("session-1")["generation"] == 1
    assert store.remove("session-1") == session


def test_training_service_status_does_not_expose_mutable_runtime_state():
    store = TrainingSessionStore({"session-1": {"generation": 1}})
    service = TrainingService(
        database=InMemoryDB(),
        game_factory=lambda *_args, **_kwargs: "game-1",
        store=store,
    )

    status = service.status("session-1")
    assert status is not None
    status["generation"] = 99

    assert store.get("session-1")["generation"] == 1


def test_training_service_creates_games_in_injected_registry():
    class BotClient:
        async def spawn_bots(self, **_kwargs):
            return BotServiceResult(ok=True)

    database = InMemoryDB()
    registry = GameRegistry()
    lifecycle = GameLifecycleService(registry)
    service = TrainingService(
        database=database,
        game_factory=lifecycle.create_game,
        bot_client_factory=BotClient,
    )

    session_id = asyncio.run(service.start(TrainingConfig(
        bot_count=1, generations=1, games_per_generation=1)))

    games = registry.list()
    assert len(games) == 1
    assert games[0].training_session_id == session_id


def test_training_services_own_independent_runtime_state():
    class BotClient:
        async def spawn_bots(self, **_kwargs):
            return BotServiceResult(ok=True)

    first_registry = GameRegistry()
    second_registry = GameRegistry()
    first_service = TrainingService(
        database=InMemoryDB(),
        game_factory=GameLifecycleService(first_registry).create_game,
        bot_client_factory=BotClient,
    )
    second_service = TrainingService(
        database=InMemoryDB(),
        game_factory=GameLifecycleService(second_registry).create_game,
        bot_client_factory=BotClient,
    )

    first_session_id = asyncio.run(first_service.start(TrainingConfig(
        bot_count=1, generations=1, games_per_generation=1)))
    second_session_id = asyncio.run(second_service.start(TrainingConfig(
        bot_count=1, generations=1, games_per_generation=1)))

    assert {
        session["session_id"] for session in first_service.list()["sessions"]
    } == {first_session_id}
    assert {
        session["session_id"] for session in second_service.list()["sessions"]
    } == {second_session_id}
    assert [game.training_session_id for game in first_registry.list()] == [
        first_session_id,
    ]
    assert [game.training_session_id for game in second_registry.list()] == [
        second_session_id,
    ]
    assert first_service.runtime.update_hub is not second_service.runtime.update_hub


def test_training_does_not_start_when_batch_persistence_fails():
    class FailingDatabase(InMemoryDB):
        def create_training_batch(self, batch_id, config) -> bool:
            raise RuntimeError("database unavailable")

    registry = GameRegistry()
    service = TrainingService(
        database=FailingDatabase(),
        game_factory=GameLifecycleService(registry).create_game,
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        asyncio.run(service.start(TrainingConfig(
            bot_count=1, generations=1, games_per_generation=1)))

    assert service.list()["sessions"] == []
    assert registry.list() == []
