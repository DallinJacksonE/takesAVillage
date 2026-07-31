import json

from service.game.serializers.game_history import build_map_hist, build_player_hist
from service.game.serializers.snapshots import (
    build_game_snapshot,
    build_night_snapshot,
    build_trade_snapshot,
    build_work_snapshot,
)


def persist_phase_completion(database, game, phase):
    if game.training:
        return
    if phase == "NIGHT":
        database.store_game_snapshot(
            game.id, game.day, phase, json.dumps(build_game_snapshot(game))
        )
    for player in game.players.values():
        if phase == "WORK":
            database.store_work_snapshot(build_work_snapshot(player, game))
        elif phase == "TRADE":
            database.store_trade_snapshot(build_trade_snapshot(player, game))
        elif phase == "NIGHT":
            database.store_night_snapshot(build_night_snapshot(player, game))


def build_completed_game_data(game):
    return {
        "map": build_map_hist(game),
        "players": build_player_hist(game),
        "training": game.training,
        "training_session_id": game.training_session_id,
        "training_generation": game.training_generation,
    }


def persist_completed_game(database, game):
    database.store_game_result(
        game.id,
        game.day,
        game.phase,
        json.dumps(build_completed_game_data(game)),
        training_batch_id=game.training_session_id if game.training else None,
        training_generation=game.training_generation,
        game_type=(
            "training" if game.training else "human_bot" if game.bot_count else "human"
        ),
        trade_count=game.trade_count,
        contest_count=game.contest_count,
        lie_count=sum(game.lie_count.values()),
    )
