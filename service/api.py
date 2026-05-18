import uuid
from flask import Blueprint, g, jsonify, make_response, request
from typing import Any, Dict, cast
from dataclasses import asdict

from db import db
from game_manager import active_games, create_game
from dtos import (
    ActiveGamesDTO, ConsentDTO, JoinableGameDTO,
    JoinGameDTO, NewGameDTO, ResearchGameDTO
)

api_bp = Blueprint('api', __name__)


@api_bp.before_request
def auto_dev_login():
    if request.path.startswith('/api/') and request.endpoint != 'api.consent':
        user_cookie = request.cookies.get('user_session')
        if not user_cookie or not db.user_exists(user_cookie):
            print("DEV MODE: Missing/Invalid cookie. Generating user session")
            new_uuid = str(uuid.uuid4())
            db.create_user(new_uuid, True)
            g.dev_user_uuid = new_uuid


@api_bp.after_request
def attach_dev_cookie(response):
    """Attach the newly generated dev cookie to the outgoing response."""
    dev_uuid = getattr(g, 'dev_user_uuid', None)
    if dev_uuid:
        response.set_cookie('user_session', dev_uuid,
                            max_age=60*60*24, secure=False, samesite='Lax')
    return response


@api_bp.route('/api/verifySession', methods=['GET'])
def verify_session():
    # Grab the cookie from the dev context or the actual request cookies
    user_cookie = getattr(g, 'dev_user_uuid',
                          None) or request.cookies.get('user_session')

    if user_cookie and db.user_exists(user_cookie):
        # Session is valid! Frontend should skip the consent screen.
        return jsonify({"userId": user_cookie, "message": "Session valid"}), 200

    # No valid session found. Frontend should show the consent screen.
    return jsonify({"error": "No valid session"}), 401


@api_bp.route('/api/consent', methods=['POST'])
def consent():
    user_uuid = str(uuid.uuid4())
    db.create_user(user_uuid, True)

    consent_dto = ConsentDTO(message="Consent logged", userId=user_uuid)
    resp = make_response(jsonify(asdict(consent_dto)))
    resp.set_cookie('user_session', user_uuid, max_age=60 *
                    60*24, secure=False, samesite='Lax')
    return resp


@api_bp.route('/api/activeGames', methods=['GET'])
def get_active_games():
    user_cookie = getattr(g, 'dev_user_uuid',
                          None) or request.cookies.get('user_session')
    if not user_cookie or not db.user_exists(user_cookie):
        return jsonify({"error": "Invalid or expired session"}), 403

    games_list = []
    rejoinable_games = []

    for game in active_games.values():
        is_user_in_game = user_cookie in game.players
        if is_user_in_game and game.status in ["WAITING", "RUNNING"]:
            rejoinable_games.append(JoinableGameDTO(
                id=game.id, name=f"Village {game.id}",
                players=f"{len(game.players)}/10", isRejoinable=True
            ))
        elif game.status == "WAITING" and not is_user_in_game:
            games_list.append(JoinableGameDTO(
                id=game.id, name=f"Village {game.id}",
                players=f"{len(game.players)}/10", isRejoinable=False
            ))

    active_games_dto = ActiveGamesDTO(games=rejoinable_games + games_list)
    return jsonify(asdict(active_games_dto))


@api_bp.route('/api/research/games', methods=['GET'])
def get_research_games():
    game_history = db.get_all_game_history()
    research_games = [
        asdict(ResearchGameDTO(**cast(Dict[str, Any], game)))
        for game in game_history
    ]
    return jsonify(research_games)


@api_bp.route('/api/newGame', methods=['POST'])
def new_game():
    user_cookie = getattr(g, 'dev_user_uuid',
                          None) or request.cookies.get('user_session')
    if not user_cookie or not db.user_exists(user_cookie):
        return jsonify({"error": "Invalid/No Session"}), 403

    # Delegate game creation strictly to the game manager
    game_id = create_game(user_cookie)

    new_game_dto = NewGameDTO(gameId=game_id)
    return jsonify(asdict(new_game_dto))


@api_bp.route('/api/joinGame', methods=['POST'])
def join_game():
    data = request.json
    game_id = data.get('gameId')
    if game_id in active_games:
        join_game_dto = JoinGameDTO(gameId=game_id)
        return jsonify(asdict(join_game_dto))
    return jsonify({"error": "Game not found"}), 404
