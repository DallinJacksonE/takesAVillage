from training_orchestrator import start_training_session, active_training_sessions
from pydantic import BaseModel
import os
import uuid
from fastapi import APIRouter, Response, Cookie, HTTPException
from typing import Optional
import ast
from pathlib import Path
from db import db
from game_manager import active_games, create_game
import httpx
import asyncio
from logger import BackendLogger

api_router = APIRouter()
CONSTANTS_DIR = Path(__file__).parent / "constants"

# Initialize the API Logger
api_logger = BackendLogger("api")


def parse_ruleset_file(filepath: Path) -> dict:
    """Safely parses a Python file and extracts KEY = VALUE assignments."""
    rules = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath.name)

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        try:
                            rules[target.id] = ast.literal_eval(node.value)
                        except ValueError as ve:
                            api_logger.warning(
                                f"Skipped '{target.id}' in "
                                f"{filepath.name}: Not a simple literal."
                            )
                            continue
    except Exception as e:
        api_logger.error(f"Error parsing {filepath.name}", exc=e)

    return rules


@api_router.get('/api/verifySession')
async def verify_session(user_session: Optional[str] = Cookie(None)):
    if user_session and db.user_exists(user_session):
        return {"userId": user_session, "message": "Session valid"}
    raise HTTPException(status_code=401, detail="No valid session")


@api_router.post('/api/consent')
async def consent(response: Response):
    user_uuid = str(uuid.uuid4())
    db.create_user(user_uuid, True)

    response.set_cookie(
        key='user_session',
        value=user_uuid,
        max_age=60*60*24,
        secure=False,
        samesite='lax'
    )
    return {"message": "Consent logged", "userId": user_uuid}


@api_router.get('/api/activeGames')
async def get_active_games(user_session: Optional[str] = Cookie(None)):
    if not user_session or not db.user_exists(user_session):
        raise HTTPException(
            status_code=403, detail="Invalid or expired session")

    games_list = []
    rejoinable_games = []

    for game in active_games.values():
        is_user_in_game = user_session in game.players
        if is_user_in_game and game.status in ["WAITING", "RUNNING"]:
            rejoinable_games.append({
                "id": game.id,
                "name": f"Village {game.id}",
                "players": f"{len(game.players)}/10",
                "isRejoinable": True
            })
        elif game.status == "WAITING" and not is_user_in_game:
            games_list.append({
                "id": game.id,
                "name": f"Village {game.id}",
                "players": f"{len(game.players)}/10",
                "isRejoinable": False
            })

    return {"games": rejoinable_games + games_list}


@api_router.get('/api/research/games')
async def get_research_games():
    game_history = db.get_all_games()
    return game_history


@api_router.post('/api/newGame')
async def new_game(payload: dict, user_session: Optional[str] = Cookie(None)):
    if not user_session or not db.user_exists(user_session):
        raise HTTPException(status_code=403, detail="Invalid/No Session")

    ruleset = payload.get('ruleset', 'default')
    bot_count = int(payload.get('botCount', 0))
    bot_genome = payload.get('botGenome', 'random')
    base_genome_data = None

    if bot_genome != "random":
        all_genomes = db.get_all_genomes()

        for g in all_genomes:
            if str(g["id"]) == str(bot_genome):
                base_genome_data = g["genome_data"]
                break

    game_id = create_game(user_session, ruleset, bot_count)

    await asyncio.sleep(1)

    # 2. Trigger the Bot Service via HTTP (Fire and Forget)
    if bot_count > 0:
        bot_url = os.environ.get(
            "BOT_SERVICE_URL", "http://bots:8001/api/spawn_bots")
        bot_secret = os.environ.get("BOT_SECRET", "default_dev_secret")

        async def spawn_external_bots():
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(bot_url, json={
                        "gameId": game_id,
                        "botCount": bot_count,
                        "botSecret": bot_secret,
                        "baseGenome": base_genome_data
                    }, timeout=5.0)
                    api_logger.info(
                        f"Successfully requested "
                        f"{bot_count} bots for {game_id}"
                    )
                except Exception as e:
                    api_logger.error("Failed to reach Bot Service", exc=e)

        asyncio.create_task(spawn_external_bots())

    return {"gameId": game_id}


@api_router.get('/api/newGame')
async def get_new_game_options():
    """Fetches the available rulesets to populate the frontend New Game Modal."""

    rulesets = {}

    constants_path = Path(__file__).resolve().parent / "constants"
    api_logger.info(f"Searching for ruleset files in: {constants_path}")

    if constants_path.exists() and constants_path.is_dir():
        for filepath in constants_path.glob("*.py"):
            if filepath.name.startswith("__"):
                continue

            ruleset_name = filepath.stem
            parsed_rules = parse_ruleset_file(filepath)
            rulesets[ruleset_name] = parsed_rules

            api_logger.info(
                f"Successfully parsed {len(parsed_rules)} "
                f"keys for {ruleset_name}"
            )
    else:
        api_logger.error(f"Constants directory NOT FOUND at {constants_path}")

    return {"options": rulesets}


@api_router.post('/api/joinGame')
async def join_game(payload: dict):
    game_id = payload.get('gameId')
    if game_id in active_games:
        return {"gameId": game_id}
    raise HTTPException(status_code=404, detail="Game not found")


class BotJoinPayload(BaseModel):
    gameId: str
    botSecret: str


@api_router.post('/api/botJoinGame')
async def bot_join_game(payload: BotJoinPayload):
    expected_secret = os.environ.get("BOT_SECRET", "default_dev_secret")

    if payload.botSecret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid bot secret")

    game_id = payload.gameId

    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = active_games[game_id]

    if game.status != "WAITING":
        raise HTTPException(status_code=400, detail="Game already running")

    bot_uuid = "bot_" + str(uuid.uuid4())[:8]

    game.add_player(bot_uuid)

    return {
        "userId": bot_uuid,
        "gameId": game_id
    }


@api_router.get('/api/research/genomes')
async def get_genomes():
    """Fetch all saved genomes. Research endpoint, no auth required."""
    # TODO get the available bot models from the bot server
    genomes = db.get_all_genomes()
    return {"genomes": genomes}


@api_router.post('/api/research/train')
async def start_training(payload: dict):
    """Start a training loop. Research endpoint, no auth required."""
    ruleset = payload.get('ruleset', 'default')
    bot_count = payload.get('botCount', 5)
    generations = payload.get('generations', 1)
    base_genome = payload.get('baseGenome', 'random')

    api_logger.info(
        f"Received training request: Ruleset={ruleset}, Bots={bot_count}, "
        f"Generations={generations}, BaseGenome={base_genome}"
    )

    asyncio.create_task(
        start_training_session(ruleset, bot_count, generations, base_genome)
    )

    return {"message": "Training sequence initiated"}


@api_router.get("/api/research/training-sessions")
async def get_training_sessions():
    sessions = []

    for session_id, session in active_training_sessions.items():
        api_logger.info(f"Session {session_id}: {session}")
        sessions.append({
            "session_id": session_id,
            "current_game_id": session.get("current_game_id"),
            "ruleset": session.get("ruleset"),
            "bot_count": session.get("bot_count"),
            "generation": session.get("generation"),
            "generations_left": session.get("generations_left"),
            "population_size": len(session.get("population", [])),
            "elite_count": session.get("elite_count"),
            "selection_size": session.get("selection_size"),
            "mutation_strength": session.get("mutation_strength"),
            "mutation_rate": session.get("mutation_rate")
        })

    return {"sessions": sessions}
