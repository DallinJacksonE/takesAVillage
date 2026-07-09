from abc import ABC, abstractmethod
import copy
from models.genetic.Relationship_manager import RelationshipManager
from models.genetic.Genome import Genome


class BaseBot(ABC):
    """
    Abstract base class handling the boilerplate of reading GameStateDTO JSON
    and formatting GameActionPayloads. Bot implementations only need to provide
    the decision-making logic.
    """
    def __init__(self, genome: Genome):
        self.genome = genome
        self.waiting = None
        # Track last seen phase to reset per-phase state
        self._last_phase = None
        # Limit how many draft trades a bot will initiate per TRADE phase
        self.trade_offers_made = 0
        self.max_trade_offers_per_phase = 2
        self.resource_map = {"Woods": "wood", "Farm": "food", "Mine": "iron"}
        # self.previous_state = None

    @abstractmethod
    def choose_action(self, game_state: dict) -> dict | None:
        """
        Must be implemented by child classes. 
        Should return a raw action dictionary, or None to finish phase.
        """
        pass

    def get_upgrade_cost(self, dev, game_state: dict):
        if dev.get("type") not in game_state.get("RESOURCE_COSTS", {}):
            return {
                "food": dev.get("level", 0),
                "wood": dev.get("level", 0),
                "iron": dev.get("level", 0) * 2 + 1
            }
        opposite = game_state.get("RESOURCE_COSTS", {}).get(dev.get("type"))
        return {
            opposite: dev.get("level", 0) * 2 + 1,
            "iron": dev.get("level", 0)
        }
    
    def get_maintenance_cost(self, dev, game_state: dict):
        if dev.get("type") not in game_state.get("RESOURCE_COSTS", {}):
            return {
                "food": dev.get("level", 0) * 2 + 1,
                "wood": dev.get("level", 0) * 2 + 1
            }
        opposite = game_state.get("RESOURCE_COSTS", {}).get(dev.get("type"))
        return {
            opposite: dev.get("level", 0),
            "iron": max(dev.get("level", 0) - 1, 0)
        }

    def is_dead_player(self, player: dict | None) -> bool:
        return not player or player.get("health") == "dead"

    def get_alive_players(self, game_state: dict) -> list[dict]:
        return [
            p for p in game_state.get("player_list", [])
            if p.get("health") != "dead"
        ]

    def find_player(self, game_state: dict, player_id: str) -> dict | None:
        return next(
            (
                p for p in game_state.get("player_list", [])
                if p.get("id") == player_id
            ),
            None
        )

    def get_available_actions(self, game_state: dict) -> list[dict]:
        """
        Reconstructs the available actions purely from the JSON state DTO.
        """
        pass

    def format_network_payload(self, action: dict | None) -> dict:
        """
        Strips internal bot metadata (keys starting with '_') and ensures
        the payload matches the strict GameActionPayload TS interface.
        """
        if not action:
            return {
                "action_command": "FINISH_PHASE",
                "payload": {}
            }

        # Strip out hidden helper keys like '_tile_type'
        clean_payload = {
            k: v for k, v in action.get("payload", {}).items()
            if not k.startswith('_')
        }

        return {
            "action_command": action["action_command"],
            "payload": clean_payload
        }
