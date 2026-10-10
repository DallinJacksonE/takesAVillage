"""Map-backed development lookup.

The authoritative Development objects live on MapTile.development. This
mapping provides the legacy dict-like API while avoiding a second store on
Game.
"""

from collections.abc import MutableMapping
from enum import Enum

from service.game.models.map import MapTile


class DevelopmentState(Enum):
    STABLE = "STABLE"
    CONTESTED = "CONTESTED"


def has_active_contest_initiation(developments, player_id):
    return any(
        development.contest_initiator_id == player_id
        and (development.is_contested or development.pending_contest)
        for development in developments.values()
    )


class MapDevelopmentStore(MutableMapping):
    def __init__(self, game):
        self.game = game

    def _items(self):
        for tile in self.game.map_data.values():
            development = getattr(tile, "development", None)
            if development is not None:
                yield development.id, development

    def __getitem__(self, key):
        development = self.get(key)
        if development is None:
            raise KeyError(key)
        return development

    def __setitem__(self, key, development):
        if development is None:
            raise ValueError("development cannot be None")
        development.id = key
        for tile in self.game.map_data.values():
            if getattr(getattr(tile, "development", None), "id", None) == key:
                tile.development = development
                return
        for tile in self.game.map_data.values():
            if getattr(tile, "development", None) is None:
                tile.development = development
                return
        tile = MapTile(f"dev_tile_{key}", 0, 0, development.type)
        tile.development = development
        self.game.map_data[tile.id] = tile

    def __delitem__(self, key):
        for tile in self.game.map_data.values():
            development = getattr(tile, "development", None)
            if getattr(development, "id", None) == key:
                tile.development = None
                return
        raise KeyError(key)

    def __iter__(self):
        return iter(dict(self._items()))

    def __len__(self):
        return len(dict(self._items()))

    def __contains__(self, key):
        return self.get(key) is not None

    def get(self, key, default=None):
        for dev_id, development in self._items():
            if dev_id == key:
                return development
        return default

    def items(self):
        return dict(self._items()).items()

    def values(self):
        return dict(self._items()).values()

    def keys(self):
        return dict(self._items()).keys()

    def pop(self, key, default=None):
        development = self.get(key)
        if development is None:
            if default is not None:
                return default
            raise KeyError(key)
        del self[key]
        return development

    def clear(self):
        for tile in self.game.map_data.values():
            tile.development = None

    def as_dict(self):
        return dict(self._items())

    def __eq__(self, other):
        return self.as_dict() == other
