from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from service.game import Game
from service.game_manager.registry import GameRegistry


class GameLifecycleService:
    def __init__(
        self,
        registry: GameRegistry,
        game_factory: Callable[..., Any] = Game,
        phase_completion_callback: Callable[..., Any] | None = None,
        id_factory: Callable[[], Any] = uuid.uuid4,
    ) -> None:
        self.registry = registry
        self.game_factory = game_factory
        self.phase_completion_callback = phase_completion_callback
        self.id_factory = id_factory

    def create_game(
        self,
        user_cookie: str,
        ruleset: str,
        bots: int = 0,
        training: bool = False,
        training_session_id: str = "",
        training_generation: int | None = None,
    ) -> str:
        game_id = "g_" + str(self.id_factory())[:4]
        game = self.game_factory(
            game_id,
            user_cookie,
            ruleset_name=ruleset,
            bots=bots,
            training=training,
            training_session_id=training_session_id,
            training_generation=training_generation,
            on_phase_completed=self.phase_completion_callback,
        )
        self.registry.add(game_id, game)
        return game_id
