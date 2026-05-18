import pytest
from app import app


@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


def test_404_error_handler(client):
    # Try to hit a route that definitely doesn't exist
    response = client.get('/api/this-route-is-fake')

    assert response.status_code == 404
    assert response.json == {"error": "API route not found"}


def test_app_configuration():
    # Ensure the app initializes with a secret key (either from config.json or fallback)
    assert app.config['SECRET_KEY'] is not None
    assert type(app.config['SECRET_KEY']) == str
