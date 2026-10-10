from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Services:
    database: Any
    game_registry: Any
    game_lifecycle: Any
    training: Any
    visualizations: Any
    bot_client: Any = None