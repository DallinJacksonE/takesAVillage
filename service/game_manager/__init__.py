"""Application services for game lifecycle, persistence, and ticking."""

from service.game_manager.bot_client import BotServiceClient, BotServiceResult
from service.game_manager.lifecycle import GameLifecycleService
from service.game_manager.loop import GameLoop
from service.game_manager.registry import GameRegistry

__all__ = [
    "BotServiceClient", "BotServiceResult", "GameLifecycleService", "GameLoop",
    "GameRegistry",
]