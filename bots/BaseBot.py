from abc import ABC, abstractmethod


class BaseBot(ABC):
    """
    Abstract base class handling the boilerplate of reading GameStateDTO JSON
    and formatting GameActionPayloads. Bot implementations only need to provide
    the decision-making logic.
    """

    @abstractmethod
    def choose_action(self, game_state: dict) -> dict | None:
        """
        Must be implemented by child classes. 
        Should return a raw action dictionary, or None to finish phase.
        """
        pass

    def get_available_actions(self, game_state: dict) -> list[dict]:
        """
        Reconstructs the available actions purely from the JSON state DTO.
        """
        actions = []
        phase = game_state.get("phase")
        me = game_state.get("me", {})
        resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})

        if phase == "WORK" and me.get("health") not in ["sick", "dead"]:
            # --- 1. BUILD ACTIONS ---
            dev_costs = game_state.get("development_costs", {})
            map_data = game_state.get("map", {})

            # Handle map_data whether it arrives as a dict or a list
            tiles = map_data.values() if isinstance(
                map_data, dict) else map_data

            for tile in tiles:
                if not tile.get("development"):
                    tile_type = tile.get("type")
                    build_cost = dev_costs.get(tile_type, {}).get("build", {})

                    affordable = all(
                        resources.get(res, 0) >= amount
                        for res, amount in build_cost.items()
                    )

                    if affordable:
                        actions.append({
                            "action_command": "BUILD_DEV",
                            "payload": {
                                "tile_id": tile["id"],
                                "_tile_type": tile_type
                            }
                        })

            # --- 2. WORK ACTIONS ---
            for job in me.get("available_work", []):
                actions.append({
                    "action_command": "COMMIT_WORK",
                    "payload": {"job": job}
                })

            # Note: Expand with UPGRADE/MAINTAIN/CONTEST checks here as needed.

        elif phase == "NIGHT":
            # --- CAMPFIRE ACTIONS ---
            fire_cost = game_state.get("campfire_cost", {"wood": 1})
            affordable = all(
                resources.get(res, 0) >= amount
                for res, amount in fire_cost.items()
            )

            if me.get("fire_status") == "COLD" and affordable:
                actions.append({
                    "action_command": "START_FIRE",
                    "payload": {}
                })

        return actions

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
