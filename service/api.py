import uuid
from fastapi import APIRouter, Response, Cookie, HTTPException
from typing import Optional

from db import db
from game_manager import active_games, create_game

api_router = APIRouter()


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
async def new_game(user_session: Optional[str] = Cookie(None)):
    if not user_session or not db.user_exists(user_session):
        raise HTTPException(status_code=403, detail="Invalid/No Session")

    game_id = create_game(user_session)
    return {"gameId": game_id}


@api_router.post('/api/joinGame')
async def join_game(payload: dict):
    game_id = payload.get('gameId')
    if game_id in active_games:
        return {"gameId": game_id}
    raise HTTPException(status_code=404, detail="Game not found")
