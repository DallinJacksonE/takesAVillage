import pytest

from service.game import game as game_module


@pytest.fixture
def make_game(monkeypatch):
    monkeypatch.setattr(game_module.random, "randint", lambda _low, _high: 0)

    def factory(player_ids=("player-1", "player-2"), *, training=True,
                ruleset="default"):
        game = game_module.Game(
            "game-1",
            player_ids[0],
            ruleset_name=ruleset,
            bots=len(player_ids),
            training=training,
        )
        for player_id in player_ids:
            game.add_player(player_id)
        return game

    return factory
