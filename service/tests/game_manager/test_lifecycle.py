from service.game_manager.lifecycle import GameLifecycleService
from service.game_manager.registry import GameRegistry


class FakeGame:
    def __init__(self, game_id, host, **kwargs):
        self.id = game_id
        self.host = host
        self.kwargs = kwargs


def test_lifecycle_creates_registered_game_with_phase_callback():
    registry = GameRegistry()
    callback = object()
    lifecycle = GameLifecycleService(
        registry=registry,
        game_factory=FakeGame,
        phase_completion_callback=callback,
        id_factory=lambda: "abcd-efgh",
    )

    game_id = lifecycle.create_game("host-1", "default", bots=2)

    assert game_id == "g_abcd"
    assert registry.get(game_id).kwargs["ruleset_name"] == "default"
    assert registry.get(game_id).kwargs["on_phase_completed"] is callback
