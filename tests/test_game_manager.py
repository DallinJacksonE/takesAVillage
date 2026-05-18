import pytest
from unittest.mock import MagicMock, patch
from game_manager import create_game, active_games, broadcast_state

# Fixture to wipe the active_games dictionary clean before every test


@pytest.fixture(autouse=True)
def reset_active_games():
    active_games.clear()
    yield


def test_create_game_adds_to_active():
    user_cookie = "session_123"
    game_id = create_game(user_cookie)

    # Assert the game ID is formatted correctly and stored
    assert game_id.startswith("g_")
    assert game_id in active_games
    assert active_games[game_id].id == game_id


def test_broadcast_state_emits_to_all_players():
    # 1. Setup a fake game with two players
    mock_game = MagicMock()
    mock_game.id = "g_test"
    mock_game.players = {"user_1": {}, "user_2": {}}
    mock_game.get_state_for_player.return_value = {"mock": "state"}

    # 2. Mock the socketio instance
    mock_socketio = MagicMock()

    # 3. Execute
    broadcast_state(mock_game, mock_socketio)

    # 4. Assert emit was called exactly twice (once per player)
    assert mock_socketio.emit.call_count == 2
