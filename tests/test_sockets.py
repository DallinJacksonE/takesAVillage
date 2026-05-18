import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from flask_socketio import SocketIO
from sockets import register_socket_events

# -------------------------------------------------------------------
# Fixtures for Setup & Mocking
# -------------------------------------------------------------------


@pytest.fixture
def app_and_socketio():
    """Creates a fresh Flask app and SocketIO instance for testing."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test_secret'
    socketio = SocketIO(app)

    # Register the events we want to test
    register_socket_events(socketio)
    return app, socketio


@pytest.fixture
def mock_game():
    """Creates a mock Game object to bypass real game logic."""
    game = MagicMock()
    game.id = "g_test"
    game.players = {}
    game.host_id = "user_1"
    game.status = "WAITING"

    # Mock return values for standard game methods
    game.get_state_for_player.return_value = {"mock_state": "loaded"}
    game.start_game.return_value = True
    game.handle_chat.return_value = True
    game.handle_action.return_value = True
    return game


@pytest.fixture
def client(app_and_socketio):
    """Provides the Flask-SocketIO test client."""
    app, socketio = app_and_socketio
    return socketio.test_client(app)


@pytest.fixture
def patch_active_games(mock_game):
    """Patches the active_games dictionary in the sockets module."""
    # We patch it where it is used (in the sockets namespace)
    mock_dict = {"g_test": mock_game}
    with patch('sockets.active_games', mock_dict):
        yield mock_dict


def test_join_room_success(client, patch_active_games, mock_game):
    """Tests that a player can successfully join an active game."""
    client.emit('join_room', {'gameId': 'g_test', 'userId': 'user_1'})
    received = client.get_received()

    # Verify the Game object's add_player method was called
    mock_game.add_player.assert_called_once_with('user_1')

    # We should receive two emissions back: 'room_update' and 'game_state'
    events = [event['name'] for event in received]
    assert 'room_update' in events
    assert 'game_state' in events


def test_rejoin_running_game_success(client, patch_active_games, mock_game):
    """Tests that an existing player can cleanly reconnect to a game in progress."""
    # 1. SETUP: The game is running, and user_1 is already registered in it
    mock_game.status = "RUNNING"
    mock_game.players = {"user_1": {}}

    # 2. ACTION: The player re-establishes their socket connection
    client.emit('join_room', {'gameId': 'g_test', 'userId': 'user_1'})
    received = client.get_received()

    # 3. ASSERT: The game should NOT try to initialize them again
    mock_game.add_player.assert_not_called()

    # 4. ASSERT: The player should receive the room update and their current game state
    events = [event['name'] for event in received]
    assert 'room_update' in events
    assert 'game_state' in events


def test_join_running_game_rejected_for_new_player(client, patch_active_games, mock_game):
    """Tests that a brand new player cannot jump into a game that has already started."""
    # 1. SETUP: The game is running, and user_2 is NOT in it
    mock_game.status = "RUNNING"
    mock_game.players = {"user_1": {}}

    # 2. ACTION: A new player tries to join
    client.emit('join_room', {'gameId': 'g_test', 'userId': 'user_2'})
    received = client.get_received()

    # 3. ASSERT: The game strictly denies adding the new player
    mock_game.add_player.assert_not_called()

    # 4. ASSERT: The client receives an explicit error event
    assert len(received) == 1
    assert received[0]['name'] == 'error'
    assert received[0]['args'][0]['message'] == 'Cannot join. Game is already in progress.'


def test_join_room_not_found(client, patch_active_games):
    """Tests joining a game that doesn't exist returns an error."""
    client.emit('join_room', {'gameId': 'g_invalid', 'userId': 'user_1'})
    received = client.get_received()

    assert len(received) == 1
    assert received[0]['name'] == 'error'
    assert received[0]['args'][0]['message'] == 'Game not found.'


def test_start_game_request_as_host(client, patch_active_games, mock_game):
    """Tests that the host can start the game."""
    client.emit('join_room', {'gameId': 'g_test', 'userId': 'user_1'})
    client.get_received()

    client.emit('start_game_request', {'gameId': 'g_test', 'userId': 'user_1'})
    received = client.get_received()

    mock_game.start_game.assert_called_once()
    assert len(received) == 1
    assert received[0]['name'] == 'game_started'
    assert received[0]['args'][0]['day'] == 1


def test_request_update(client, patch_active_games, mock_game):
    """Tests that a player can request their specific game state."""
    client.emit('request_update', {'gameId': 'g_test', 'userId': 'user_1'})
    received = client.get_received()

    mock_game.get_state_for_player.assert_called_with('user_1')
    assert len(received) == 1
    assert received[0]['name'] == 'game_state'
    assert received[0]['args'][0] == {"mock_state": "loaded"}


@patch('sockets.broadcast_state')
def test_send_chat(mock_broadcast, client, patch_active_games, mock_game):
    """Tests that sending a chat forwards to the game and triggers a broadcast."""
    payload = {'gameId': 'g_test', 'userId': 'user_1',
               'message': 'Hello Village'}
    client.emit('send_chat', payload)

    mock_game.handle_chat.assert_called_once_with('user_1', payload)
    mock_broadcast.assert_called_once()


@patch('sockets.broadcast_state')
def test_submit_action_success(mock_broadcast, client, patch_active_games, mock_game):
    """Tests that a valid action triggers the game logic and broadcasts state."""
    # Ensure our mock returns True (action accepted)
    mock_game.handle_action.return_value = True
    payload = {'gameId': 'g_test', 'userId': 'user_1',
               'action_command': 'BUILD_DEV'}

    client.emit('submit_action', payload)

    mock_game.handle_action.assert_called_once_with('user_1', payload)
    mock_broadcast.assert_called_once()


@patch('sockets.broadcast_state')
def test_submit_action_rejected(mock_broadcast, client, patch_active_games, mock_game):
    """Tests that an invalid action emits an error back to the specific user."""
    mock_game.handle_action.return_value = False
    payload = {'gameId': 'g_test', 'userId': 'user_1',
               'actionCommand': 'ILLEGAL_MOVE'}

    # 1. Have the test client join the scoped room first
    client.emit('join_room', {'gameId': 'g_test', 'userId': 'user_1'})
    client.get_received()  # Clear the queue

    # 2. Now submit the illegal action
    client.emit('submit_action', payload)
    received = client.get_received()

    assert mock_broadcast.called is False
    assert len(received) == 1
    assert received[0]['name'] == 'error'
    assert received[0]['args'][0]['message'] == 'Action rejected by game rules.'
    assert received[0]['args'][0]['action_command'] == 'ILLEGAL_MOVE'
