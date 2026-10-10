import importlib


def test_game_domain_is_available_through_package_paths():
    game_package = importlib.import_module("service.game")
    default_rules = importlib.import_module("service.game.constants.default")
    player_module = importlib.import_module("service.game.models.player")
    development_module = importlib.import_module(
        "service.game.models.development"
    )
    state_module = importlib.import_module("service.game.serializers.state")
    history_module = importlib.import_module(
        "service.game.serializers.game_history"
    )
    snapshots_module = importlib.import_module(
        "service.game.serializers.snapshots"
    )

    assert game_package.Game.__module__ == "service.game.game"
    assert default_rules.GAME_LENGTH > 0
    assert player_module.Player.__module__ == "service.game.models.player"
    assert development_module.Development.__module__ == (
        "service.game.models.development"
    )
    assert callable(state_module.build_player_state)
    assert callable(history_module.build_player_hist)
    assert callable(snapshots_module.build_game_snapshot)
