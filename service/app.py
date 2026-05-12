if True:
    from gevent import monkey
    monkey.patch_all()

from game import Game
from dtos import (
    ActiveGamesDTO, ConsentDTO, JoinableGameDTO,
    JoinGameDTO, NewGameDTO, ResearchGameDTO
)
from db import db
from serializers.game_info_builder import build_map_hist, build_player_hist
from flask_socketio import SocketIO, emit, join_room
from flask import Flask, g, jsonify, make_response, request
from typing import Any, Dict, cast
import uuid
import time
import os
import json
from dataclasses import asdict


app = Flask(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, 'config.json')

try:
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        app.config['SECRET_KEY'] = config_data['flask']['secret_key']
except (FileNotFoundError, KeyError):
    app.config['SECRET_KEY'] = 'dev_fallback_key'

socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")
active_games = {}


def broadcast_state(game):
    """Helper to send individualized states to all players in a game."""
    for pid in game.players.keys():
        socketio.emit(
            'game_state',
            game.get_state_for_player(pid),
            # STRICT SEPARATION: Scoped to this specific game
            to=f"{game.id}_{pid}"
        )


def game_loop():
    while True:
        for game in list(active_games.values()):
            if game.status == "ACTIVE":
                if game.check_timer():
                    print("Next phase")
                    broadcast_state(game)
            elif game.status == "ENDED":
                map_dict = build_map_hist(game)
                player_dict = build_player_hist(game)
                db.store_game_result(map_dict, player_dict)

                del active_games[game.id]

        time.sleep(1)


socketio.start_background_task(game_loop)


@app.before_request
def auto_dev_login():
    """DEV OVERRIDE: Automatically create a user if Chrome blocks the cookie."""
    if request.path.startswith('/api/') and request.endpoint != 'consent':
        user_cookie = request.cookies.get('user_session')
        if not user_cookie or not db.user_exists(user_cookie):
            print("🔧 DEV MODE: Missing/Invalid cookie. Auto-generating user session...")
            new_uuid = str(uuid.uuid4())
            db.create_user(new_uuid, True)
            g.dev_user_uuid = new_uuid


@app.after_request
def attach_dev_cookie(response):
    """Attach the newly generated dev cookie to the outgoing response."""
    dev_uuid = getattr(g, 'dev_user_uuid', None)
    if dev_uuid:
        response.set_cookie('user_session', dev_uuid,
                            max_age=60*60*24, secure=False, samesite='Lax')
    return response

# --- HTTP Routes ---


@app.route('/api/consent', methods=['POST'])
def consent():
    user_uuid = str(uuid.uuid4())
    db.create_user(user_uuid, True)

    consent_dto = ConsentDTO(message="Consent logged", userId=user_uuid)
    resp = make_response(jsonify(asdict(consent_dto)))
    resp.set_cookie('user_session', user_uuid, max_age=60 *
                    60*24, secure=False, samesite='Lax')

    return resp


@app.route('/api/activeGames', methods=['GET'])
def get_active_games():
    user_cookie = getattr(g, 'dev_user_uuid',
                          None) or request.cookies.get('user_session')

    if not user_cookie or not db.user_exists(user_cookie):
        return jsonify({"error": "Invalid or expired session"}), 403

    games_list = []
    rejoinable_games = []  # Store separately to push to the top

    for game in active_games.values():
        is_user_in_game = user_cookie in game.players

        # Check if the user is already in this game
        if is_user_in_game and game.status in ["WAITING", "ACTIVE"]:
            rejoinable_games.append(JoinableGameDTO(
                id=game.id,
                name=f"Village {game.id}",
                players=f"{len(game.players)}/10",
                isRejoinable=True
            ))
        # Otherwise, standard check for joinable waiting games
        elif game.status == "WAITING" and not is_user_in_game:
            games_list.append(JoinableGameDTO(
                id=game.id,
                name=f"Village {game.id}",
                players=f"{len(game.players)}/10",
                isRejoinable=False
            ))

    # Combine lists: Rejoinable games go first
    active_games_dto = ActiveGamesDTO(games=rejoinable_games + games_list)
    return jsonify(asdict(active_games_dto))


@app.route('/api/research/games', methods=['GET'])
def get_research_games():
    game_history = db.get_all_game_history()

    # We cast 'game' to a Dict with string keys to
    # satisfy the strict type checker
    research_games = [
        asdict(ResearchGameDTO(**cast(Dict[str, Any], game)))
        for game in game_history
    ]

    return jsonify(research_games)


@app.route('/api/newGame', methods=['POST'])
def new_game():
    # Grab the injected dev UUID, or fall back to the cookie
    user_cookie = getattr(g, 'dev_user_uuid',
                          None) or request.cookies.get('user_session')

    if not user_cookie or not db.user_exists(user_cookie):
        return jsonify({"error": "Invalid/No Session"}), 4

    game_id = "g_" + str(uuid.uuid4())[:4]
    active_games[game_id] = Game(game_id, user_cookie)

    new_game_dto = NewGameDTO(gameId=game_id)
    return jsonify(asdict(new_game_dto))


@app.route('/api/joinGame', methods=['POST'])
def join_game():
    data = request.json
    game_id = data.get('gameId')
    if game_id in active_games:
        join_game_dto = JoinGameDTO(gameId=game_id)
        return jsonify(asdict(join_game_dto))
    return jsonify({"error": "Game not found"}), 404


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "API route not found"}), 404


# --- WebSocket Events ---


@socketio.on('join_room')
def on_join(data):
    game_id = data.get('gameId')
    user_id = data.get('userId')

    # 1. PURGE: Remove the player from any other active games to prevent zombie loops
    for g_id, g in list(active_games.items()):
        if g_id != game_id and user_id in g.players:
            del g.players[user_id]

            # Optional Memory Cleanup: If the old game is now empty, delete it
            if len(g.players) == 0:
                del active_games[g_id]

    if game_id in active_games:
        game = active_games[game_id]
        game.add_player(user_id)

        join_room(game_id)
        # 2. SCOPE: Player joins a private room specifically for this game instance
        join_room(f"{game_id}_{user_id}")

        emit('room_update', {"player_count": len(game.players)}, to=game_id)

        # 3. DIRECT EMIT: Ensure the initial state goes to the scoped room
        emit('game_state', game.get_state_for_player(
            user_id), to=f"{game_id}_{user_id}")
    else:
        emit('error', {'message': 'Game not found.'})


@socketio.on('start_game_request')
def on_start(data):
    game_id = data.get('gameId')
    user_id = data.get('userId')
    if game_id in active_games:
        game = active_games[game_id]
        if game.host_id == user_id:
            if game.start_game():
                emit('game_started', {"day": 1}, to=game_id)


@socketio.on('request_update')
def on_request_update(data):
    game_id = data.get('gameId')
    user_id = data.get('userId')
    if game_id in active_games:
        game = active_games[game_id]
        state = game.get_state_for_player(user_id)
        emit('game_state', state)

# --- SEPARATED WEBSOCKET ROUTING ---


@socketio.on('send_chat')
def on_send_chat(data):
    """Handles pure social interactions."""
    game_id = data.get('gameId')
    user_id = data.get('userId') or data.get('from_id')

    if game_id in active_games:
        game = active_games[game_id]
        if game.handle_chat(user_id, data):
            broadcast_state(game)


@socketio.on('submit_action')
def on_submit_action(data):
    """Handles all game state changes (building, committing, contracts)."""
    game_id = data.get('gameId')
    user_id = data.get('userId')

    if game_id in active_games:
        game = active_games[game_id]
        if game.handle_action(user_id, data):
            broadcast_state(game)


if __name__ == '__main__':
    # Add host="0.0.0.0" so Docker can route external traffic to it
    socketio.run(app, host="0.0.0.0", debug=True, port=5000)
