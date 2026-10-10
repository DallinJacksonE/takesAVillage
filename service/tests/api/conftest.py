import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from service.api.dependencies import Services
from service.api.router import create_api_router
from service.db import InMemoryDB
from service.game_manager.lifecycle import GameLifecycleService
from service.game_manager.registry import GameRegistry
from service.research.training.service import TrainingService
from service.research.training.session_store import TrainingSessionStore


class _NoopVisualizations:
    def ensure(self, *_args):
        return []


class _TestDatabase(InMemoryDB):
    registry: GameRegistry
    training_sessions: dict


@pytest.fixture
def api_context():
    database = _TestDatabase()
    registry = GameRegistry()
    lifecycle = GameLifecycleService(registry)
    sessions = {}
    training = TrainingService(
        database=database,
        store=TrainingSessionStore(sessions),
        game_factory=lifecycle.create_game,
    )
    database.registry = registry
    database.training_sessions = sessions

    app = FastAPI()
    app.include_router(create_api_router(Services(
        database=database,
        game_registry=registry,
        game_lifecycle=lifecycle,
        training=training,
        visualizations=_NoopVisualizations(),
    )))
    with TestClient(app) as client:
        yield client, database

