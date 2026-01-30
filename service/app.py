from flask import Flask, request, jsonify, make_response
from flask_socketio import SocketIO, join_room, emit, leave_room
from game import Game
from db import db
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'research_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for active games (RAM is faster than DB for real-time)
active_games = {}

# --- HTTP Routes ---


@app.route('/api/consent', methods=['POST'])
def consent():
    # Generate a persistent user cookie
    user_uuid = str(uuid.uuid4())
    resp = make_response(
        jsonify({"message": "Consent logged", "userId": user_uuid}))
    resp.set_cookie('user_session', user_uuid, max_age=60*60*24*365)  # 1 year

    # Log to DB
    db.create_user(user_uuid, True)
    return resp


@app.route('/api/newGame', methods=['POST'])
def new_game():
    user_cookie = request.cookies.get('user_session')
    if not user_cookie:
        return jsonify({"error": "No consent cookie"}), 403

    game_id = "g_" + str(uuid.uuid4())[:8]  # Short ID for display
    new_game_obj = Game(game_id, user_cookie)
    active_games[game_id] = new_game_obj

    return jsonify({"gameId": game_id})


@app.route('/api/joinGame', methods=['POST'])
def join_game():
    # In a real app, you might validate if the game exists here
    # But often we just handle the actual join logic in the websocket connect
    data = request.json
    game_id = data.get('gameId')
    if game_id in active_games:
        return jsonify({"gameId": game_id, "status": "Found"})
    return jsonify({"error": "Game not found"}), 404

# --- WebSocket Events ---


@socketio.on('join_room')
def on_join(data):
    game_id = data['gameId']
    user_id = data['userId']  # Sent from client cookie reading

    if game_id in active_games:
        game = active_games[game_id]
        game.add_player(user_id)

        join_room(game_id)

        # Broadcast updated waiting list to everyone in the room
        emit('room_update', {"player_count": len(game.players)}, room=game_id)

        # Send initial state to the user joining
        emit('game_state', game.get_state_for_player(user_id))


@socketio.on('start_game_request')
def on_start(data):
    game_id = data['gameId']
    user_id = data['userId']

    if game_id in active_games:
        game = active_games[game_id]
        # Verify host
        if game.host_id == user_id:
            success = game.start_game()
            if success:
                # Broadcast to everyone that game has started
                # We must iterate and send custom state to each player so they don't see
                # hidden info (if applicable), or just send generic 'START' signal
                # For now, we trigger a refresh
                for pid in game.players:
                    # Note: In real SocketIO, mapping session_id to socket_sid is needed
                    # for individual messaging. For simplicity, we broadcast update.
                    pass
                emit('game_started', {"day": 1}, room=game_id)


@socketio.on('request_update')
def on_request_update(data):
    game_id = data['gameId']
    user_id = data['userId']
    if game_id in active_games:
        game = active_games[game_id]
        state = game.get_state_for_player(user_id)
        emit('game_state', state)


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
