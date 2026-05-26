import time
import json
import uuid
from db import db
from game import Game
from serializers.game_info_builder import build_map_hist, build_player_hist

# Single source of truth for all active games
active_games = {}


def create_game(user_cookie: str) -> str:
    """Creates a new game instance and adds it to the active pool."""
    game_id = "g_" + str(uuid.uuid4())[:4]
    active_games[game_id] = Game(game_id, user_cookie)
    return game_id


def broadcast_state(game, socketio):
    """Helper to send individualized states to all players in a game."""
    for pid in game.players.keys():
        socketio.emit(
            'game_state',
            game.get_state_for_player(pid),
            to=f"{game.id}_{pid}"
        )


def game_loop(socketio):
    """The main loop managing phase transitions and game endings."""
    while True:
        for game in list(active_games.values()):
            if game.status == "RUNNING" and game.check_timer():
                print("Next phase")
                broadcast_state(game, socketio)
            elif game.status == "ENDED":
                map_dict = build_map_hist(game)
                player_dict = build_player_hist(game)

                # 1. Combine the history dicts into a single payload
                game_data = {
                    "map": map_dict,
                    "players": player_dict
                }

                # 2. Pass the game.id and the stringified JSON payload
                db.store_game_result(
                    game.id,
                    game.day,
                    game.phase,
                    json.dumps(game_data)
                )

                del active_games[game.id]

        time.sleep(1)
