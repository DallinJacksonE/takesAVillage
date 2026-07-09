import asyncio
import json
import uuid
from db import db
from game import Game
from serializers.game_info_builder import build_map_hist, build_player_hist
from logger import BackendLogger

gm_logger = BackendLogger("game_manager")
active_games = {}


def create_game(user_cookie: str, ruleset: str, bots=0,
                training=False, training_session_id="",
                training_generation=None) -> str:
    """Creates a new game instance and adds it to the active pool."""
    game_id = "g_" + str(uuid.uuid4())[:4]
    active_games[game_id] = Game(
        game_id, user_cookie, ruleset_name=ruleset, bots=bots,
        training=training, training_session_id=training_session_id,
        training_generation=training_generation)
    return game_id


async def game_loop(connection_manager):
    """The main loop managing phase transitions and game endings."""
    while True:
        for game in list(active_games.values()):
            if game.status == "RUNNING":
                if game.check_timer():
                    gm_logger.info(
                        f"Game {game.id} transitioning to next phase")
                    await connection_manager.broadcast_game_state(
                        game.id,
                        game
                    )

            elif game.status == "ENDED":
                map_dict = build_map_hist(game)
                player_dict = build_player_hist(game)

                from training_orchestrator import handle_training_game_ended

                game_data = {
                    "map": map_dict,
                    "players": player_dict,
                    "training": game.training,
                    "training_session_id": game.training_session_id,
                    "training_generation": game.training_generation
                }

                db.store_game_result(
                    game.id,
                    game.day,
                    game.phase,
                    json.dumps(game_data),
                    training_batch_id=game.training_session_id if game.training else None,
                    training_generation=game.training_generation,
                    game_type=("training" if game.training else
                               "human_bot" if game.bot_count else "human"),
                    trade_count=game.trade_count,
                    contest_count=game.contest_count,
                    lie_count=sum(game.lie_count.values())
                )

                if game.training:
                    asyncio.create_task(
                        handle_training_game_ended(
                            game.id, game.training_session_id)
                    )

                del active_games[game.id]
        await asyncio.sleep(.1)
