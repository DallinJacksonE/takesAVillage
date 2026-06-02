import uuid
from fastapi import APIRouter, Response, Cookie, HTTPException
from typing import Optional
import ast
from pathlib import Path
from db import db
from game_manager import active_games, create_game

api_router = APIRouter()
CONSTANTS_DIR = Path(__file__).parent / "constants"


def parse_ruleset_file(filepath: Path) -> dict:
    """Safely parses a Python file and extracts KEY = VALUE assignments."""
    rules = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            # Parse the file into an Abstract Syntax Tree
            tree = ast.parse(f.read(), filename=filepath.name)

        for node in tree.body:
            # Look for assignment operations (e.g., KEY = VALUE)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    # Ensure the target is a variable name
                    if isinstance(target, ast.Name):
                        try:
                            # Safely evaluate the right side of the equals sign
                            # This handles strings, numbers, booleans, lists, and dicts
                            rules[target.id] = ast.literal_eval(node.value)
                        except ValueError:
                            # Skip complex expressions (like function calls or math operations)
                            # since ast.literal_eval only evaluates python literals
                            continue
    except Exception as e:
        print(f"Error parsing {filepath.name}: {e}")

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
    game_history = db.get_all_game_history()
    return game_history


@api_router.post('/api/newGame')
async def new_game(payload: dict, user_session: Optional[str] = Cookie(None)):
    if not user_session or not db.user_exists(user_session):
        raise HTTPException(status_code=403, detail="Invalid/No Session")

    # Extract the payload values sent by the frontend, providing safe defaults
    ruleset = payload.get('ruleset', 'default')
    bot_count = payload.get('botCount', 0)

    # Pass the new parameters to the game manager
    game_id = create_game(user_session, ruleset, bot_count)
    return {"gameId": game_id}


@api_router.get('/api/newGame')
async def new_game_options(user_session: Optional[str] = Cookie(None)):
    if not user_session or not db.user_exists(user_session):
        raise HTTPException(status_code=403, detail="Invalid/No Session")

    options = {}

    # Ensure the directory exists to prevent crashes
    if CONSTANTS_DIR.exists() and CONSTANTS_DIR.is_dir():
        # Iterate through all .py files in the directory
        for filepath in CONSTANTS_DIR.glob("*.py"):
            # Skip the __init__.py file
            if filepath.name == "__init__.py":
                continue

            # Use the filename (without .py) as the dictionary key
            rule_type = filepath.stem
            options[rule_type] = parse_ruleset_file(filepath)

    return {"options": options}


@api_router.post('/api/joinGame')
async def join_game(payload: dict):
    game_id = payload.get('gameId')
    if game_id in active_games:
        return {"gameId": game_id}
    raise HTTPException(status_code=404, detail="Game not found")
