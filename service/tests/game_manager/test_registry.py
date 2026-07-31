from service.game_manager.registry import GameRegistry


def test_registry_owns_game_collection_without_exposing_mutable_storage():
    registry = GameRegistry()
    game = object()

    registry.add("game-1", game)

    assert registry.get("game-1") is game
    assert registry.list() == [game]
    assert registry.contains("game-1")
    assert registry.remove("game-1") is game
    assert registry.get("game-1") is None
