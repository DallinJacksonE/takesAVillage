from training_orchestrator import start_training_session, active_training_sessions
from pydantic import BaseModel
import os
import uuid
from fastapi import APIRouter, Response, Cookie, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional
import ast
from pathlib import Path
from db import db
from game_manager import active_games, create_game
import httpx
import asyncio
from logger import BackendLogger
from training_session_presenter import build_training_session_payload
from training_updates import training_update_hub
from research_visualizations.batch_commands import default_batch_visualization_commands
from research_visualizations.game_commands import default_game_visualization_commands
from research_visualizations.registry import VisualizationRegistry
from research_visualizations.runner import VisualizationRunner

api_router = APIRouter()
CONSTANTS_DIR = Path(__file__).parent / "constants"

# Initialize the API Logger
api_logger = BackendLogger("api")


def ensure_visualizations(scope_type: str, scope_id: str, context: dict):
    existing = db.get_research_visualizations(scope_type, scope_id)
    if existing:
        return existing

    commands = (default_game_visualization_commands()
                if scope_type == "game"
                else default_batch_visualization_commands())
    try:
        VisualizationRunner(db, VisualizationRegistry(commands)).run_all(
            scope_type, scope_id, context)
    except Exception as e:
        api_logger.warning(
            f"Failed to generate {scope_type} visualizations for {scope_id}: {e}")
    return db.get_research_visualizations(scope_type, scope_id)


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
async def get_research_games(search: Optional[str] = None,
                             sort: str = "time_desc"):
    game_history = db.get_all_games()
    if search:
        query = search.lower()
        game_history = [
            game for game in game_history
            if query in str(game.get("game_id", "")).lower()
            or query in str(game.get("game_type", "")).lower()
            or query in str(game.get("training_batch_id", "")).lower()
        ]
    if sort == "name_asc":
        game_history = sorted(game_history, key=lambda game: game.get("game_id", ""))
    elif sort == "name_desc":
        game_history = sorted(
            game_history, key=lambda game: game.get("game_id", ""), reverse=True)
    return game_history


@api_router.get('/api/research/games/{game_id}')
async def get_research_game(game_id: str):
    for game in db.get_all_games():
        if game.get("game_id") == game_id:
            return {
                **game,
                "visualizations": ensure_visualizations("game", game_id, game),
            }
    raise HTTPException(status_code=404, detail="Game not found")


@api_router.get('/api/research/training-batches')
async def get_training_batches():
    persisted_batches = db.get_training_batches()
    persisted_ids = {batch.get("batch_id") for batch in persisted_batches}
    active_payload = build_training_session_payload(active_training_sessions)
    active_batches = []
    for session in active_payload.get("sessions", []):
        if session.get("session_id") in persisted_ids:
            continue
        active_batches.append({
            "batch_id": session.get("session_id"),
            "status": "running",
            "ruleset": session.get("ruleset"),
            "bot_count": session.get("bot_count"),
            "current_generation": session.get("generation"),
            "current_game_id": session.get("current_game_id"),
            "generation_statistics": session.get("generation_statistics", []),
        })
    return {"batches": active_batches + persisted_batches}


@api_router.get('/api/research/training-batches/{batch_id}')
async def get_training_batch(batch_id: str):
    batch = db.get_training_batch(batch_id)
    if not batch:
        session = active_training_sessions.get(batch_id)
        if not session:
            raise HTTPException(status_code=404, detail="Training batch not found")
        batch = {"batch_id": batch_id, "status": "running", **session}
    return {
        **batch,
        "visualizations": ensure_visualizations("training_batch", batch_id, batch),
    }


@api_router.get('/api/research/visualizations/{visualization_id}')
async def get_research_visualization(visualization_id: str):
    visualization = db.get_research_visualization(visualization_id)
    if not visualization:
        raise HTTPException(status_code=404, detail="Visualization not found")
    return Response(
        content=visualization["image_bytes"],
        media_type=visualization.get("mime_type", "image/png"),
    )


@api_router.post('/api/newGame')
async def new_game(payload: dict, user_session: Optional[str] = Cookie(None)):
    if not user_session or not db.user_exists(user_session):
        raise HTTPException(status_code=403, detail="Invalid/No Session")

    ruleset = payload.get('ruleset', 'default')
    bot_count = int(payload.get('botCount', 0))
    bot_genome = payload.get('botGenome', 'random')
    bot_model = payload.get('botModel', 'genetic')  # <-- Extract the model
    base_genome_data = None

    if bot_genome != "random":
        all_genomes = db.get_all_genomes()
        for g in all_genomes:
            if str(g["id"]) == str(bot_genome):
                base_genome_data = g["genome_data"]
                break

    game_id = create_game(user_session, ruleset, bot_count)

    if bot_count > 0:
        bot_url = os.environ.get(
            "BOT_SERVICE_URL", "http://bots:8001")
        bot_secret = os.environ.get("BOT_SECRET", "default_dev_secret")

        async def spawn_external_bots():
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(f"{bot_url}/api/spawn_bots", json={
                        "gameId": game_id,
                        "botCount": bot_count,
                        "botSecret": bot_secret,
                        "baseGenome": base_genome_data,
                        "botModel": bot_model  # <-- Pass to Bot Server
                    }, timeout=5.0)
                    api_logger.info(f"Successfully requested {bot_count} "
                                    f"{bot_model} bots for {game_id}")
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
    """Fetch all saved genomes and dynamically available bot models."""
    genomes = db.get_all_genomes()
    models = ["genetic"]  # Fallback model
    bot_url = os.environ.get("BOT_SERVICE_URL", "http://bots:8001")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{bot_url}/api/models", timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", ["genetic"])
                api_logger.info(f"Successfully fetched "
                                f"{len(models)} bot models.")
        except Exception as e:
            api_logger.warning(
                f"Failed to fetch models from Bot Server."
                f"Falling back to default. \n{e}")

    return {"genomes": genomes, "models": models}


@api_router.post('/api/research/train')
async def start_training(payload: dict):
    """Start a training loop. Research endpoint, no auth required."""
    ruleset = payload.get('ruleset', 'default')
    bot_count = int(payload.get('botCount', 5))
    generations = int(payload.get('generations', 1))
    base_genome = payload.get('baseGenome', 'random')
    bot_model = payload.get('botModel', 'genetic')  # <-- Extract the model
    mutation_strength = float(payload.get('mutationStrength', 0.25))
    mutation_rate = float(payload.get('mutationRate', 0.15))
    random_immigrant_count = int(payload.get('randomImmigrantCount', 1))

    api_logger.info(
        f"Received training request: Ruleset={ruleset}, Bots={bot_count}, "
        f"Generations={generations}, "
        f"BaseGenome={base_genome}, Model={bot_model}"
    )

    asyncio.create_task(
        # <-- Pass the model to the orchestrator
        start_training_session(
            ruleset, bot_count, generations, base_genome, bot_model,
            mutation_strength=mutation_strength,
            mutation_rate=mutation_rate,
            random_immigrant_count=random_immigrant_count)
    )

    return {"message": "Training sequence initiated"}


@api_router.get("/api/research/training-sessions")
async def get_training_sessions():
    return build_training_session_payload(active_training_sessions)


@api_router.websocket("/ws/research/training-sessions")
async def training_sessions_websocket(websocket: WebSocket):
    await training_update_hub.connect(websocket)
    await training_update_hub.send_current_state(websocket, active_training_sessions)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        training_update_hub.disconnect(websocket)
    except Exception as e:
        api_logger.error("Research training websocket failed", exc=e)
        training_update_hub.disconnect(websocket)
