import asyncio
from types import SimpleNamespace

from service.game_manager.loop import GameLoop
from service.game_manager.registry import GameRegistry


def test_ended_game_is_persisted_and_removed_even_when_callback_fails():
    registry = GameRegistry()
    game = SimpleNamespace(id="game-1", status="ENDED", training=True,
                           training_session_id="batch-1")
    registry.add(game.id, game)
    persisted = []

    async def failing_callback(_game_id, _session_id):
        raise RuntimeError("callback failed")

    loop = GameLoop(
        registry=registry,
        persist_completed=lambda ended: persisted.append(ended.id),
        broadcaster=SimpleNamespace(broadcast_game_state=lambda *_args: None),
        training_completion_callback=failing_callback,
    )

    asyncio.run(loop.tick_once())

    assert persisted == ["game-1"]
    assert registry.get("game-1") is None


def test_ended_game_is_retained_until_persistence_succeeds():
    registry = GameRegistry()
    game = SimpleNamespace(id="game-1", status="ENDED", training=False)
    registry.add(game.id, game)
    attempts = []

    def persist(ended):
        attempts.append(ended.id)
        if len(attempts) == 1:
            raise RuntimeError("temporary database outage")

    loop = GameLoop(
        registry=registry,
        persist_completed=persist,
        broadcaster=SimpleNamespace(broadcast_game_state=lambda *_args: None),
    )

    asyncio.run(loop.tick_once())
    assert registry.get("game-1") is game

    asyncio.run(loop.tick_once())
    assert attempts == ["game-1", "game-1"]
    assert registry.get("game-1") is None


def test_training_completion_does_not_block_other_game_ticks():
    async def scenario():
        registry = GameRegistry()
        game = SimpleNamespace(id="game-1", status="ENDED", training=True,
                               training_session_id="batch-1")
        registry.add(game.id, game)
        release = asyncio.Event()

        async def slow_callback(_game_id, _session_id):
            await release.wait()

        loop = GameLoop(
            registry=registry,
            persist_completed=lambda _game: None,
            broadcaster=SimpleNamespace(broadcast_game_state=lambda *_args: None),
            training_completion_callback=slow_callback,
        )

        await asyncio.wait_for(loop.tick_once(), timeout=0.1)
        assert registry.get("game-1") is None
        release.set()
        await asyncio.gather(*loop._training_tasks)

    asyncio.run(scenario())
