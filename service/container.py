import os

import httpx

from service.api.dependencies import Services
from service.api.websocket.connection_manager import ConnectionManager
from service.db import db
from service.game_manager.bot_client import BotServiceClient
from service.game_manager.lifecycle import GameLifecycleService
from service.game_manager.persistence import persist_phase_completion
from service.game_manager.registry import GameRegistry
from service.research.training.service import TrainingService
from service.research.visualizations.service import VisualizationService


class AppContainer:
    def __init__(self, database=None):
        self.database = database or db
        self.registry = GameRegistry()
        self.lifecycle = GameLifecycleService(
            self.registry,
            phase_completion_callback=lambda game, phase: persist_phase_completion(
                self.database, game, phase),
        )
        self.bot_client = BotServiceClient(
            os.environ.get("BOT_SERVICE_URL", "http://bots:8001"),
            os.environ.get("BOT_SECRET", ""),
            httpx.AsyncClient,
        )
        self.training = TrainingService(
            database=self.database,
            game_factory=self.lifecycle.create_game,
            bot_client_factory=lambda: self.bot_client,
        )
        self.visualizations = VisualizationService(self.database)
        self.connections = ConnectionManager(self.registry)

    def api_services(self):
        return Services(
            database=self.database,
            game_registry=self.registry,
            game_lifecycle=self.lifecycle,
            training=self.training,
            visualizations=self.visualizations,
            bot_client=self.bot_client,
        )
