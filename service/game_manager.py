import asyncio
import json
import uuid
from db import db
from game import Game
from serializers.game_info_builder import build_map_hist, build_player_hist

# Single source of truth for all active games
active_games = {}


def create_game(user_cookie: str, ruleset: str, bots=0) -> str:
    """Creates a new game instance and adds it to the active pool."""
    game_id = "g_" + str(uuid.uuid4())[:4]
    active_games[game_id] = Game(
        game_id, user_cookie, ruleset_name=ruleset, bots=bots)
    return game_id


async def game_loop(connection_manager):
    """The main loop managing phase transitions and game endings."""
    while True:
        for game in list(active_games.values()):
            if game.status == "RUNNING":
                print("running bot turns")

                game.check_all_players_locked()

                if game.check_timer():
                    print("Next phase")
                    await connection_manager.broadcast_game_state(
                        game.id,
                        game
                    )

            elif game.status == "ENDED":
                map_dict = build_map_hist(game)
                player_dict = build_player_hist(game)

                # Combine the history dicts into a single payload
                game_data = {
                    "map": map_dict,
                    "players": player_dict
                }

                # Pass the game.id and the stringified JSON payload
                db.store_game_result(
                    game.id,
                    game.day,
                    game.phase,
                    json.dumps(game_data)
                )

                del active_games[game.id]

        # Non-blocking sleep lets FastAPI handle other requests concurrently
        await asyncio.sleep(1)
