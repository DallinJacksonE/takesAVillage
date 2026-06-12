from abc import ABC, abstractmethod


class BaseBot(ABC):
    """
    Abstract base class handling the boilerplate of reading GameStateDTO JSON
    and formatting GameActionPayloads. Bot implementations only need to provide
    the decision-making logic.
    """
    def __init__(self):
        self.waiting = None
        # Track last seen phase to reset per-phase state
        self._last_phase = None
        # Limit how many draft trades a bot will initiate per TRADE phase
        self.trade_offers_made = 0
        self.max_trade_offers_per_phase = 2

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

        # reset per-phase counters when phase changes
        if phase != self._last_phase:
            self._last_phase = phase
            if phase == "TRADE":
                self.trade_offers_made = 0

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

                owner = self.find_player(game_state, dev["owner_id"])
                if self.is_dead_player(owner):
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
                owner_id = job.get('development', {}).get('owner_id')
                owner = self.find_player(game_state, owner_id)
                if self.is_dead_player(owner):
                    continue
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

        elif phase == "TRADE" and me.get("health") != "dead":
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
                    # Determine which side we are on and propose feasible
                        # actual_items for the shipping window (don't overpromise)
                        is_initiator = action.get("initiator_id") == me.get("id")
                        promised = action.get("offer_items") if is_initiator else action.get("request_items")

                        feasible = {}
                        resources = me.get("resources", {})
                        for r, qty in (promised or {}).items():
                            try:
                                q = int(qty)
                            except Exception:
                                q = 0
                            available = int(resources.get(r, 0))
                            send_amt = max(0, min(q, available))
                            if send_amt > 0:
                                feasible[r] = send_amt

                        actions.append({
                            "action_command": "FINALIZE",
                            "payload": {
                                "action_id": action["id"],
                                "actual_items": feasible
                            }
                        })
            # --- 1. Draft simple trades ---
            # Bots may propose trades to other players offering surplus
            # and requesting resources they lack.
            resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})
            # determine offer (most abundant) and request (least abundant)
            sorted_res = sorted(resources.items(), key=lambda kv: kv[1])
            if sorted_res:
                request_res = sorted_res[0][0]
                offer_res = sorted_res[-1][0]
                offer_amt = max(1, resources.get(offer_res, 0) // 2)

                if resources.get(offer_res, 0) >= 1:
                    # Don't create new offers if we already have an outstanding
                    # outgoing trade (pending/negotiating/accepted).
                    existing_outgoing_trade = any(
                        a.get("type") == "TRADE" and a.get("initiator_id") == me.get("id")
                        and a.get("status") in ["PENDING", "NEGOTIATING", "ACCEPTED"]
                        for a in me.get("actions", [])
                    )

                    if existing_outgoing_trade:
                        # Respect a single outstanding trade until it's resolved
                        pass
                    else:
                        # Throttle number of trades per bot per TRADE phase
                        if self.trade_offers_made < self.max_trade_offers_per_phase:
                            for player in self.get_alive_players(game_state):
                                if player.get("id") == me.get("id"):
                                    continue

                                # Avoid creating duplicate pending trades to same target
                                existing = any(
                                    a.get("type") == "TRADE" and a.get("target_id") == player.get("id")
                                    for a in me.get("actions", [])
                                )
                                if existing:
                                    continue

                                actions.append({
                                    "action_command": "TRADE",
                                    "payload": {
                                        "type": "TRADE",
                                        "target_id": player.get("id"),
                                        "offer_items": {offer_res: offer_amt},
                                        "request_items": {request_res: 1}
                                    }
                                })
                                # Count this draft so we don't spam the phase
                                self.trade_offers_made += 1
                                # Stop creating more offers once limit reached
                                if self.trade_offers_made >= self.max_trade_offers_per_phase:
                                    break
                

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
                    # Only offer ACCEPT when the host still has seats available
                    is_request = action.get("is_request", False)
                    host_id = action.get("target_id") if is_request else action.get("initiator_id")
                    host_player = None
                    for p in game_state.get("player_list", []):
                        if p.get("id") == host_id:
                            host_player = p
                            break

                    can_accept = False
                    if host_player and host_player.get("fire_status") == "HOST":
                        max_seats = game_state.get("max_fire_seats", 0)
                        current = len(host_player.get("fire_guests", []) or [])
                        if current < max_seats:
                            can_accept = True

                    if can_accept:
                        actions.append({
                            "action_command": "ACCEPT",
                            "payload": {
                                "action_id": action["id"]
                            }
                        })

                    # Always allow denying an invite
                    actions.append({
                        "action_command": "DENY",
                        "payload": {
                            "action_id": action["id"]
                        }
                    })
            
            for player in self.get_alive_players(game_state):
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
