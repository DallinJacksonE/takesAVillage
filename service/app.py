from flask import Flask, request, jsonify, make_response
from flask_socketio import SocketIO, join_room, emit, leave_room
from game import Game
from db import db
import uuid
import json
import os
import threading
import time

app = Flask(__name__)

# Load config
base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, 'config.json')

try:
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        app.config['SECRET_KEY'] = config_data['flask']['secret_key']
except (FileNotFoundError, KeyError):
    print("WARNING: Using unsafe default secret key. Create config.json to fix.")
    app.config['SECRET_KEY'] = 'dev_fallback_key'

socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for active games
active_games = {}

# --- Background Timer Thread ---


def game_loop():
    """Checks active games every second to see if the phase timer expired."""
    while True:
        # Convert to list to avoid runtime error if dict changes size during iteration
        for game in list(active_games.values()):
            if game.state == "RUNNING":
                if game.check_timer():
                    # Timer expired, phase changed. Broadcast update.
                    # We reuse 'game_started' to trigger a client-side fetch.
                    socketio.emit('game_started', {
                                  "day": game.day}, room=game.game_id)
        time.sleep(1)


# Start the background thread
threading.Thread(target=game_loop, daemon=True).start()


# --- HTTP Routes ---

@app.route('/api/consent', methods=['POST'])
def consent():
    user_uuid = str(uuid.uuid4())
    resp = make_response(
        jsonify({"message": "Consent logged", "userId": user_uuid}))
    resp.set_cookie('user_session', user_uuid, max_age=60*60*24)
    db.create_user(user_uuid, True)
    return resp


@app.route('/api/activeGames', methods=['GET'])
def get_active_games():
    user_cookie = request.cookies.get('user_session')
    if not user_cookie or not db.user_exists(user_cookie):
        return jsonify({"error": "Invalid or expired session"}), 403

    games_list = []
    for game_id, game in active_games.items():
        if game.state == "WAITING":
            games_list.append({
                "id": game.game_id,
                "name": f"Village {game.game_id}",
                "players": f"{len(game.players)}/10"
            })
    return jsonify(games_list)


@app.route('/api/newGame', methods=['POST'])
def new_game():
    user_cookie = request.cookies.get('user_session')
    if not user_cookie or not db.user_exists(user_cookie):
        return jsonify({"error": "Invalid/No Session"}), 403

    game_id = "g_" + str(uuid.uuid4())[:8]
    active_games[game_id] = Game(game_id, user_cookie)
    return jsonify({"gameId": game_id})


@app.route('/api/joinGame', methods=['POST'])
def join_game():
    data = request.json
    game_id = data.get('gameId')
    if game_id in active_games:
        return jsonify({"gameId": game_id, "status": "Found"})
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
        emit('room_update', {"player_count": len(game.players)}, room=game_id)
        emit('game_state', game.get_state_for_player(user_id))
    else:
        emit('error', {'message': 'Game not found. Server may have restarted.'})


@socketio.on('start_game_request')
def on_start(data):
    game_id = data.get('gameId')
    user_id = data.get('userId')

    if game_id in active_games:
        game = active_games[game_id]
        if game.host_id == user_id:
            if game.start_game():
                emit('game_started', {"day": 1}, room=game_id)


@socketio.on('request_update')
def on_request_update(data):
    game_id = data.get('gameId')
    user_id = data.get('userId')
    if game_id in active_games:
        game = active_games[game_id]
        state = game.get_state_for_player(user_id)
        emit('game_state', state)

# --- NEW IMPLEMENTATIONS FOR GAMEPLAY.JSX ---


@socketio.on('send_message')
def on_send_message(data):
    """Handles composing new messages (Text, Trade, Employment)."""
    game_id = data.get('gameId')
    user_id = data.get('from_id')

    if game_id in active_games:
        game = active_games[game_id]
        # Calls the game logic to create the message object
        if game.create_message(user_id, data):
            # Trigger refresh for everyone in the room so they see the new message
            emit('game_started', {}, room=game_id)


@socketio.on('update_message')
def on_update_message(data):
    """Handles Accept, Deny, Barter actions."""
    game_id = data.get('gameId')
    user_id = data.get('userId')

    if game_id in active_games:
        game = active_games[game_id]
        # Calls game logic to change message status/values
        if game.handle_message_update(user_id, data['msgId'], data['action'], data.get('values')):
            emit('game_started', {}, room=game_id)


@socketio.on('user_action')
def on_user_action(data):
    """Handles generic game actions like Building, takeing, finishing phase"""
    game_id = data.get('gameId')
    user_id = data.get('userId')
    action = data.get('action')
    payload = data.get('payload')

    if game_id in active_games:
        game = active_games[game_id]

        # Call the game logic
        if game.handle_user_action(user_id, action, payload):
            # If successful, broadcast update to everyone
            emit('game_started', {}, room=game_id)


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
