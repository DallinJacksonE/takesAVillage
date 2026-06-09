from training_orchestrator import start_training_session
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
api_router = APIRouter()
CONSTANTS_DIR = Path(__file__).parent / "constants"


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
                            # DIAGNOSTIC: See exactly which variables are being rejected
                            print(f"⚠️ Skipped '{target.id}' in "
                                  f"{filepath.name}: Not a simple literal.")
                            continue
    except Exception as e:
        print(f"❌ Error parsing {filepath.name}: {e}")

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
                        "botSecret": bot_secret
                    }, timeout=5.0)
                    print(f"[api/newGame bot request] Successfully requested"
                          f"{bot_count} bots for {game_id}")
                except Exception as e:
                    print(f"⚠️ Failed to reach Bot Service: {e}")

        asyncio.create_task(spawn_external_bots())

    return {"gameId": game_id}


@api_router.get('/api/newGame')
async def get_new_game_options(user_session: Optional[str] = Cookie(None)):
    """Fetches the available rulesets to populate the frontend New Game Modal."""
    if not user_session or not db.user_exists(user_session):
        raise HTTPException(status_code=403, detail="Invalid/No Session")

    rulesets = {}

    # DIAGNOSTIC: Force an absolute path resolution to guarantee Docker finds the folder
    constants_path = Path(__file__).resolve().parent / "constants"
    print(f"Searching for ruleset files in: {constants_path}")

    if constants_path.exists() and constants_path.is_dir():
        for filepath in constants_path.glob("*.py"):
            if filepath.name.startswith("__"):
                continue

            ruleset_name = filepath.stem
            print(f"Found ruleset file: {filepath.name}")

            parsed_rules = parse_ruleset_file(filepath)
            rulesets[ruleset_name] = parsed_rules

            print(f"✅ Successfully parsed "
                  f"{len(parsed_rules)} keys for '{ruleset_name}'")
    else:
        print(f"❌ Constants directory NOT FOUND at {constants_path}")

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
    # Use an environment variable for the secret, with a fallback for local dev
    expected_secret = os.environ.get("BOT_SECRET", "default_dev_secret")

    if payload.botSecret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid bot secret")

    game_id = payload.gameId

    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = active_games[game_id]

    # Optional: Prevent bots from joining games that have already started
    if game.status != "WAITING":
        raise HTTPException(status_code=400, detail="Game already running")

    # Generate a distinct prefix so it's easy to identify bots in logs/DB
    bot_uuid = "bot_" + str(uuid.uuid4())[:8]

    # Pre-register the bot in the game state
    game.add_player(bot_uuid)

    return {
        "userId": bot_uuid,
        "gameId": game_id
    }


@api_router.get('/api/research/genomes')
async def get_genomes():
    genomes = db.get_all_genomes()
    return {"genomes": genomes}


@api_router.post('/api/research/train')
async def start_training(payload: dict, user_session: Optional[str] = Cookie(None)):
    if not user_session or not db.user_exists(user_session):
        raise HTTPException(status_code=403, detail="Invalid/No Session")

    ruleset = payload.get('ruleset', 'default')
    bot_count = payload.get('botCount', 5)
    generations = payload.get('generations', 1)
    base_genome = payload.get('baseGenome', 'random')

    print(f"[API] Received request for training loop:"
          f"{generations} gens, {bot_count} bots, base: {base_genome}")

    # THE MISSING PIECE: Fire and forget the orchestrator
    asyncio.create_task(
        start_training_session(ruleset, bot_count, generations, base_genome)
    )

    return {"message": "Training sequence initiated"}
