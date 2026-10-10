from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from typing import Any

from service.game_manager.registry import GameRegistry
from service.logging import BackendLogger


class GameLoop:
    def __init__(
        self,
        registry: GameRegistry,
        persist_completed: Callable[[Any], Any],
        broadcaster: Any,
        training_completion_callback: Callable[[str, str], Awaitable[Any]] | None = None,
        training_orphan_cleanup_callback: Callable[[str], Awaitable[Any]] | None = None,
        logger: Any | None = None,
        state_sync_interval: float = 1.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.registry = registry
        self.persist_completed = persist_completed
        self.broadcaster = broadcaster
        self.training_completion_callback = training_completion_callback
        self.training_orphan_cleanup_callback = training_orphan_cleanup_callback
        self._training_orphaned_since: dict[str, float] = {}
        self.logger = logger or BackendLogger("game_manager")
        self.state_sync_interval = state_sync_interval
        self._clock = clock
        self._last_state_sync: dict[str, float] = {}
        self._completing: set[str] = set()
        self._training_tasks: set[asyncio.Task] = set()

    async def _send_queued_notifications(self, game: Any) -> None:
        sender = getattr(self.broadcaster, "send_personal_message", None)
        if sender is None or not hasattr(game, "drain_notifications"):
            return
        for player_id in list(getattr(game, "players", {})):
            for notification in game.drain_notifications(player_id):
                result = sender({
                    "event": "game_notification",
                    "data": notification,
                }, game.id, player_id)
                if inspect.isawaitable(result):
                    await result

    async def _notify_training(self, game_id: str, session_id: str) -> None:
        callback = self.training_completion_callback
        if callback is None:
            return
        try:
            await callback(game_id, session_id)
        except Exception as exc:
            self.logger.error(
                f"Training completion failed for {game_id}", exc=exc)

    async def _cleanup_orphaned_training_game(self, game: Any) -> bool:
        """Remove a training game when all of its websockets have disappeared."""
        if not getattr(game, "training", False):
            return False

        has_connections = getattr(self.broadcaster, "has_connections", None)
        if has_connections is None or has_connections(game.id):
            self._training_orphaned_since.pop(game.id, None)
            return False

        # A game can briefly have no sockets while bots are starting. Give it a
        # small grace period, then treat a connection-less training game as
        # abandoned. This prevents orphaned Game objects from living forever.
        first_missing = self._training_orphaned_since.setdefault(game.id, time.monotonic())
        if time.monotonic() - first_missing < 5.0:
            return False

        self.logger.warning(
            f"Cleaning orphaned training game {game.id}: no active websockets")
        callback = self.training_orphan_cleanup_callback
        if callback is not None:
            try:
                await callback(game.id)
            except Exception as exc:
                self.logger.error(
                    f"Failed to cancel orphaned training game {game.id}", exc=exc)
        else:
            await self.broadcaster.disconnect_game(game.id)
            self.registry.remove(game.id)
        self._training_orphaned_since.pop(game.id, None)
        return True

    async def tick_once(self) -> None:
        for game in self.registry.list():
            if await self._cleanup_orphaned_training_game(game):
                continue
            if game.status == "RUNNING":
                now = self._clock()
                last_sync = self._last_state_sync.setdefault(game.id, now)
                if game.check_timer():
                    try:
                        result = self.broadcaster.broadcast_game_state(
                            game.id, game, changed=True)
                        if inspect.isawaitable(result):
                            await result
                        self._last_state_sync[game.id] = now
                        await self._send_queued_notifications(game)
                    except Exception as exc:
                        self.logger.error(
                            f"Failed to broadcast game state for {game.id}", exc=exc)
                elif (
                    now - last_sync >= self.state_sync_interval
                    and self._has_connections(game.id)
                ):
                    try:
                        result = self.broadcaster.broadcast_game_state(
                            game.id, game, changed=False)
                        if inspect.isawaitable(result):
                            await result
                        self._last_state_sync[game.id] = now
                    except Exception as exc:
                        self.logger.error(
                            f"Failed to synchronize game state for {game.id}",
                            exc=exc,
                        )
                continue
            if game.status != "ENDED" or game.id in self._completing:
                continue
            self._completing.add(game.id)
            try:
                try:
                    self.persist_completed(game)
                except Exception as exc:
                    self.logger.error(f"Failed to persist completed game {game.id}", exc=exc)
                    # Keep the ended game registered so a later tick can retry.
                    # Removing it here would turn a transient DB outage into
                    # permanent game-history loss.
                    continue
                if game.training:
                    self._training_orphaned_since.pop(game.id, None)
                    disconnect_game = getattr(self.broadcaster, "disconnect_game", None)
                    if disconnect_game is not None:
                        await disconnect_game(game.id)
                if game.training and self.training_completion_callback:
                    task = asyncio.create_task(self._notify_training(
                        game.id, game.training_session_id))
                    self._training_tasks.add(task)
                    task.add_done_callback(self._training_tasks.discard)
            finally:
                self._completing.discard(game.id)

            self.registry.remove(game.id)
            self._last_state_sync.pop(game.id, None)

    def _has_connections(self, game_id: str) -> bool:
        checker = getattr(self.broadcaster, "has_connections", None)
        return checker(game_id) if checker else True

    async def run(self, interval_seconds: float = 0.1) -> None:
        while True:
            await self.tick_once()
            await asyncio.sleep(interval_seconds)
