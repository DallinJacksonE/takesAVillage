from abc import ABC, abstractmethod


class BaseBot(ABC):
    """
    Abstract base class handling the boilerplate of reading GameStateDTO JSON
    and formatting GameActionPayloads. Bot implementations only need to provide
    the decision-making logic.
    """
    def __init__(self):
        self.waiting = None

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

    def get_available_actions(self, game_state: dict) -> list[dict]:
        """
        Reconstructs the available actions purely from the JSON state DTO.
        """
        if game_state.get("status") == "WAITING":
            return []
        actions = []
        phase = game_state.get("phase")
        me = game_state.get("me", {})
        resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})

        pending_application = any(
            action.get("type") == "EMPLOYMENT"
            and action.get("is_application")
            and action.get("initiator_id") == me.get("id")
            and action.get("status") == "PENDING"
            for action in me.get("actions", [])
        )

        if pending_application:
            self.waiting = True
            return []
        
        self.waiting = False

        if phase == "WORK" and me.get("health") not in ["sick", "recovering", "dead"]:
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
            for dev in game_state.get("developments", []):
                if dev["owner_id"] == me["id"] and dev["can_upgrade"]:
                    upgrade_cost = self.get_upgrade_cost(dev, game_state)

                    affordable = all(
                        resources.get(res, 0) >= amount
                        for res, amount in upgrade_cost.items()
                    )

                    if affordable:
                        actions.append({
                            "action_command": "UPGRADE_DEV",
                            "payload": {
                                "dev_id": dev["id"]
                            }
                        })
            
                if dev["owner_id"] == me["id"]:
                    affordable = all(
                        resources.get(r, 0) >= amt
                        for r, amt in self.get_maintenance_cost(dev, game_state).items()
                    )

                    if affordable:
                        actions.append({
                            "action_command": "MAINTAIN_DEV",
                            "payload": {
                                "dev_id": dev["id"]
                            }
                        })
            
                if dev["owner_id"] != me["id"]:
                    actions.append({
                        "action_command": "CONTEST_DEV",
                        "payload": {
                            "dev_id": dev["id"],
                            "side": "INITIATOR"
                        }
                    })

            # --- JOB APPLICATIONS ---

            existing_apps = {
                (a.get("dev_id"), a.get("target_id"))
                for a in me.get("actions", [])
                if a["type"] == "EMPLOYMENT"
            }

            for dev in game_state.get("developments", []):

                if (dev['id'], dev['owner_id']) in existing_apps:
                    continue

                if dev["owner_id"] == me["id"]:
                    continue

                if dev.get("worker_id"):
                    continue

                if dev.get("is_contested"):
                    continue

                actions.append({
                    "action_command": "EMPLOYMENT",
                    "payload": {
                        "type": "EMPLOYMENT",
                        "target_id": dev["owner_id"],
                        "dev_id": dev["id"],
                        "wage": dev['level'],
                        "wage_type": dev['type'],
                        "is_application": True
                    }
                })

            # --- 2. WORK ACTIONS ---
            for job in me.get("available_work", []):
                if not job.get('development').get('is_contested'):
                    actions.append({
                        "action_command": "COMMIT_WORK",
                        "payload": {"job": job}
                    })
            
            for action in me.get("actions", []):
                if (
                    action["type"] == "EMPLOYMENT"
                    and action["status"] == "PENDING"
                    and action["target_id"] == me["id"]
                ):
                    actions.append({
                        "action_command": "ACCEPT",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })
                    actions.append({
                        "action_command": "DENY",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })

        elif phase == "TRADE":
            for action in me.get("actions", []):
                if (
                    action["type"] == "TRADE"
                    and action["waiting_on_id"] == me["id"]
                ):
                    actions.append({
                        "action_command": "ACCEPT",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })
                    actions.append({
                        "action_command": "DENY",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })
                if action["status"] == "ACCEPTED":
                    actions.append({
                        "action_command": "FINALIZE",
                        "payload": {
                            "action_id": action["id"],
                            "actual_items": action["offer_items"]
                        }
                    })
                

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
            for action in me.get("actions", []):
                if (
                    action["type"] == "CAMPFIRE"
                    and action["waiting_on_id"] == me["id"]
                ):
                    actions.append({
                        "action_command": "ACCEPT",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })
                    actions.append({
                        "action_command": "DENY",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })
            
            for player in game_state["player_list"]:
                if player["id"] == me["id"]:
                    continue
                if me["fire_status"] == "HOST":
                    actions.append({
                        "action_command": "CAMPFIRE",
                        "payload": {
                            "target_id": player["id"],
                            "is_request": False,
                            "type": "CAMPFIRE"
                        }
                    })
                
                elif player["fire_status"] == "HOST" and me["fire_status"] == "COLD":
                    actions.append({
                        "action_command": "CAMPFIRE",
                        "payload": {
                            "target_id": player["id"],
                            "is_request": True,
                            "type": "CAMPFIRE"
                        }
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
