from flask import request
from flask_socketio import emit, join_room
from game_manager import active_games, broadcast_state


def register_socket_events(socketio):

    @socketio.on('join_room')
    def on_join(data):
        game_id = data.get('gameId')
        user_id = data.get('userId')

        # 1. PURGE: Remove the player from any other active games
        for g_id, g in list(active_games.items()):
            if g_id != game_id and user_id in g.players:
                del g.players[user_id]
                if len(g.players) == 0:
                    del active_games[g_id]

        if game_id in active_games:
            game = active_games[game_id]

            # 2. REJOIN SAFEGUARD: Only add them if they aren't already in the game
            if user_id not in game.players:
                # Prevent entirely new players from joining a game in progress
                if game.status != "WAITING":
                    emit('error', {
                         'message': 'Cannot join. Game is already in progress.'}, to=request.sid)
                    return

                # It's a new player in a waiting game, safe to initialize them
                game.add_player(user_id)

            join_room(game_id)
            # 3. SCOPE: Player joins a private room
            join_room(f"{game_id}_{user_id}")

            emit('room_update', {"player_count": len(
                game.players)}, to=game_id)

            # 4. DIRECT EMIT: Send the current state back to the reconnected player
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
            emit('game_state', game.get_state_for_player(user_id))

    @socketio.on('send_chat')
    def on_send_chat(data):
        game_id = data.get('gameId')
        user_id = data.get('userId') or data.get('from_id')

        if game_id in active_games:
            game = active_games[game_id]
            if game.handle_chat(user_id, data):
                broadcast_state(game, socketio)

    @socketio.on('submit_action')
    def on_submit_action(data):
        game_id = data.get('gameId')
        user_id = data.get('userId')

        if game_id in active_games:
            game = active_games[game_id]
            if game.handle_action(user_id, data):
                broadcast_state(game, socketio)
            else:
                action_command = data.get('action_command') or data.get(
                    'actionId') or data.get('actionCommand')
                emit('error', {
                    'message': 'Action rejected by game rules.',
                    'action_command': action_command
                }, to=f"{game_id}_{user_id}")
