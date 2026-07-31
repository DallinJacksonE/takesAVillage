from __future__ import annotations

from collections.abc import Iterator
from typing import Any


class GameRegistry:
    """Owns the mutable collection of active games."""

    def __init__(self) -> None:
        self._games: dict[str, Any] = {}

    def add(self, game_id: str, game: Any) -> None:
        self._games[game_id] = game

    def create(self, game: Any) -> Any:
        self.add(game.id, game)
        return game

    def get(self, game_id: str, default: Any = None) -> Any:
        return self._games.get(game_id, default)

    def list(self) -> list[Any]:
        return list(self._games.values())

    def remove(self, game_id: str) -> Any:
        return self._games.pop(game_id, None)

    def pop(self, game_id: str, default: Any = None) -> Any:
        return self._games.pop(game_id, default)

    def keys(self):
        return self._games.keys()

    def contains(self, game_id: str) -> bool:
        return game_id in self._games

    def clear(self) -> None:
        self._games.clear()

    def __contains__(self, game_id: object) -> bool:
        return game_id in self._games

    def __getitem__(self, game_id: str) -> Any:
        return self._games[game_id]

    def __setitem__(self, game_id: str, game: Any) -> None:
        self.add(game_id, game)

    def __delitem__(self, game_id: str) -> None:
        del self._games[game_id]

    def __iter__(self) -> Iterator[str]:
        return iter(self._games)

    def __len__(self) -> int:
        return len(self._games)

    def values(self):
        return self._games.values()

    def items(self):
        return self._games.items()
