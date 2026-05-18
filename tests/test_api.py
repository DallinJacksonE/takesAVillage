import pytest
from flask import Flask
from unittest.mock import patch
from api import api_bp


@pytest.fixture
def client():
    # Spin up a lightweight, fake Flask app just for testing the blueprint
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    app.testing = True

    with app.test_client() as client:
        yield client


@patch('api.db')
def test_consent_route_generates_cookie(mock_db, client):
    # Mock the DB so it doesn't actually try to hit a real database
    mock_db.create_user.return_value = True

    # Fire a request at the route
    response = client.post('/api/consent')

    # Assertions
    assert response.status_code == 200
    assert 'user_session' in response.headers.get('Set-Cookie', '')
    assert b'Consent logged' in response.data


@patch('api.db')
@patch('api.create_game')
def test_new_game_route(mock_create_game, mock_db, client):
    # Setup our mocks
    mock_db.user_exists.return_value = True
    mock_create_game.return_value = "g_mocked"

    # We must explicitly set a cookie since the route checks for one
    client.set_cookie('user_session', 'test_cookie')

    response = client.post('/api/newGame')

    assert response.status_code == 200
    assert response.json['gameId'] == "g_mocked"
