import ast
import asyncio
import hmac
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException

from service.api.schemas.games import BotJoinRequest, JoinGameRequest, NewGameRequest
from service.game_manager.bot_client import BotServiceClient

CONSTANTS_DIR = Path(__file__).resolve().parents[2] / "game" / "constants"


def _parse_ruleset(path: Path):
    rules = {}
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        rules[target.id] = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        pass
    return rules


def create_router(services):
    router = APIRouter()

    @router.get("/api/activeGames")
    async def active_games(user_session: Optional[str] = Cookie(None)):
        if not user_session or not services.database.user_exists(user_session):
            raise HTTPException(status_code=403, detail="Invalid or expired session")
        public, rejoinable = [], []
        for game in services.game_registry.list():
            item = {"id": game.id, "name": f"Village {game.id}",
                    "players": f"{len(game.players)}/10"}
            if user_session in game.players and game.status in ("WAITING", "RUNNING"):
                rejoinable.append({**item, "isRejoinable": True})
            elif game.status == "WAITING" and user_session not in game.players:
                public.append({**item, "isRejoinable": False})
        return {"games": rejoinable + public}

    @router.post("/api/newGame")
    async def new_game(payload: NewGameRequest,
                       user_session: Optional[str] = Cookie(None)):
        if not user_session or not services.database.user_exists(user_session):
            raise HTTPException(status_code=403, detail="Invalid/No Session")
        genome = None
        if payload.botGenome != "random":
            for item in services.database.get_all_genomes():
                if str(item["id"]) == str(payload.botGenome):
                    genome = item["genome_data"]
                    break
        game_id = services.game_lifecycle.create_game(
            user_session, payload.ruleset, bots=payload.botCount)
        if payload.botCount > 0 and services.bot_client:
            client = services.bot_client() if callable(services.bot_client) else services.bot_client
            asyncio.create_task(client.spawn_bots(
                game_id, payload.botCount, genome, payload.botModel, timeout=5.0))
        return {"gameId": game_id}

    @router.get("/api/newGame")
    async def new_game_options():
        options = {}
        if CONSTANTS_DIR.is_dir():
            for path in CONSTANTS_DIR.glob("*.py"):
                if not path.name.startswith("__"):
                    options[path.stem] = _parse_ruleset(path)
        return {"options": options}

    @router.post("/api/joinGame")
    async def join_game(payload: JoinGameRequest):
        if services.game_registry.contains(payload.gameId):
            return {"gameId": payload.gameId}
        raise HTTPException(status_code=404, detail="Game not found")

    @router.post("/api/botJoinGame")
    async def bot_join_game(payload: BotJoinRequest):
        expected_secret = os.environ.get("BOT_SECRET")
        if (not expected_secret
                or not hmac.compare_digest(payload.botSecret, expected_secret)):
            raise HTTPException(status_code=403, detail="Invalid bot secret")
        game = services.game_registry.get(payload.gameId)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        if game.status != "WAITING":
            raise HTTPException(status_code=400, detail="Game already running")
        bot_id = "bot_" + str(uuid.uuid4())[:8]
        game.add_player(bot_id)
        return {"userId": bot_id, "gameId": payload.gameId}

    return router
