from dtos import (
    ConsentDTO, ActiveGamesDTO, JoinableGameDTO,
    ResearchGameDTO, NewGameDTO, JoinGameDTO
)
from dataclasses import asdict
from flask import Flask, request, jsonify, make_response
from flask_socketio import SocketIO, join_room, emit
from game import Game
from db import db
import uuid
import json
import os
import threading
import time
from typing import Dict, Any, cast

app = Flask(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, 'config.json')

try:
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        app.config['SECRET_KEY'] = config_data['flask']['secret_key']
except (FileNotFoundError, KeyError):
    app.config['SECRET_KEY'] = 'dev_fallback_key'

socketio = SocketIO(app, cors_allowed_origins="*")
active_games = {}


def game_loop():
    while True:
        for game in list(active_games.values()):
            if game.state == "RUNNING":
                if game.check_timer():
                    socketio.emit(
                        'game_started',
                        {"day": game.day},
                        to=game.game_id
                    )
        time.sleep(1)


threading.Thread(target=game_loop, daemon=True).start()

# --- HTTP Routes ---


@app.route('/api/consent', methods=['POST'])
def consent():
    user_uuid = str(uuid.uuid4())
    db.create_user(user_uuid, True)

    consent_dto = ConsentDTO(message="Consent logged", userId=user_uuid)
    resp = make_response(jsonify(asdict(consent_dto)))
    resp.set_cookie('user_session', user_uuid, max_age=60*60*24)

    return resp


@app.route('/api/activeGames', methods=['GET'])
def get_active_games():
    user_cookie = request.cookies.get('user_session')
    if not user_cookie or not db.user_exists(user_cookie):
        return jsonify({"error": "Invalid or expired session"}), 403

    games_list = []
    # Fixed unused game_id variable by iterating values
    for game in active_games.values():
        if game.state == "WAITING":
            games_list.append(JoinableGameDTO(
                id=game.game_id,
                name=f"Village {game.game_id}",
                players=f"{len(game.players)}/10"
            ))

    active_games_dto = ActiveGamesDTO(games=games_list)
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
    user_cookie = request.cookies.get('user_session')
    if not user_cookie or not db.user_exists(user_cookie):
        return jsonify({"error": "Invalid/No Session"}), 403

    game_id = "g_" + str(uuid.uuid4())[:8]
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

# --- WebSocket Events ---


@socketio.on('join_room')
def on_join(data):
    game_id = data.get('gameId')
    user_id = data.get('userId')
    if game_id in active_games:
        game = active_games[game_id]
        game.add_player(user_id)
        join_room(game_id)
        emit('room_update', {"player_count": len(game.players)}, to=game_id)
        emit('game_state', game.get_state_for_player(user_id))
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

# --- UNIFIED MESSAGE HANDLER ---


@socketio.on('send_message')
def on_send_message(data):
    game_id = data.get('gameId')
    user_id = data.get('from_id') or data.get('userId')

    if game_id in active_games:
        game = active_games[game_id]
        if game.handle_message_action(user_id, data):
            emit('game_started', {}, to=game_id)


@socketio.on('user_action')
def on_user_action(data):
    game_id = data.get('gameId')
    user_id = data.get('userId')
    action = data.get('action')
    payload = data.get('payload')

    if game_id in active_games:
        game = active_games[game_id]
        if game.handle_user_action(user_id, action, payload):
            emit('game_started', {}, to=game_id)


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
