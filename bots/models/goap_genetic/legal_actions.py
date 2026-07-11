from .domain import Command
from .goap_genome import GOAPGenome
from .memory import Memory


RESOURCE_TYPES = ("food", "wood", "iron")
DEVELOPMENT_RESOURCE = {"Farm": "food", "Woods": "wood", "Mine": "iron"}


class GOAPLegalActionSource:
    """Builds concrete legal server actions for GOAP bots.

    This class is intentionally model-local and policy-light. It derives the
    finite action candidates that the GOAP planner can score without using the
    legacy GeneticBot relationship manager or marginal-utility helpers.
    """

    def __init__(self, genome: GOAPGenome, max_trade_offers_per_phase: int = 2):
        self.genome = genome
        self.max_trade_offers_per_phase = max_trade_offers_per_phase
        self._last_phase = None
        self._trade_offers_made = 0

    def available_actions(self, game_state: dict,
                          memory: Memory | None = None) -> list[dict]:
        if game_state.get("status") == "WAITING":
            return []

        me = self._me(game_state)
        if self._is_dead_player(me):
            return []

        phase = game_state.get("phase")
        self._reset_phase_state(phase)

        if phase == "WORK":
            return self._work_actions(game_state, me)
        if phase == "TRADE":
            return self._trade_actions(game_state, me, memory)
        if phase == "NIGHT":
            return self._night_actions(game_state, me)
        return []

    def _reset_phase_state(self, phase: str | None) -> None:
        if phase == self._last_phase:
            return
        self._last_phase = phase
        if phase == "TRADE":
            self._trade_offers_made = 0

    def _work_actions(self, game_state: dict, me: dict) -> list[dict]:
        actions = []
        resources = self._resources(me)

        if me.get("health") not in ["sick", "recovering"]:
            actions.extend(self._build_actions(game_state, resources))
            actions.extend(self._development_actions(game_state, me, resources))
            actions.extend(self._employment_application_actions(game_state, me))
            actions.extend(self._commit_work_actions(game_state, me))

        actions.extend(self._pending_employment_response_actions(me))
        return actions

    def _build_actions(self, game_state: dict, resources: dict) -> list[dict]:
        actions = []
        for tile in self._map_tiles(game_state):
            if tile.get("development"):
                continue
            tile_type = tile.get("type")
            build_cost = self._development_build_cost(tile_type, game_state)
            if self._is_affordable(build_cost, resources):
                actions.append({
                    "action_command": Command.BUILD_DEV,
                    "payload": {
                        "tile_id": tile.get("id"),
                        "_tile_type": tile_type,
                    },
                })
        return actions

    def _development_actions(self, game_state: dict, me: dict,
                             resources: dict) -> list[dict]:
        actions = []
        my_id = me.get("id")
        for dev in game_state.get("developments", []) or []:
            dev_id = dev.get("id")
            if not dev_id:
                continue

            if dev.get("owner_id") == my_id:
                if dev.get("can_upgrade") and self._is_affordable(
                        self._upgrade_cost(dev, game_state), resources):
                    actions.append({
                        "action_command": Command.UPGRADE_DEV,
                        "payload": {"dev_id": dev_id},
                    })

                if self._is_affordable(
                        self._maintenance_cost(dev, game_state), resources):
                    actions.append({
                        "action_command": Command.MAINTAIN_DEV,
                        "payload": {"dev_id": dev_id},
                    })

                if dev.get("is_contested"):
                    actions.append({
                        "action_command": Command.CONTEST_DEV,
                        "payload": {"dev_id": dev_id, "side": "OWNER"},
                    })
                continue

            if dev.get("is_contested") and dev.get("contest_initiator_id") == my_id:
                actions.append({
                    "action_command": Command.CONTEST_DEV,
                    "payload": {"dev_id": dev_id, "side": "CONTESTER"},
                })
            elif dev.get("owner_id") != my_id:
                actions.append({
                    "action_command": Command.CONTEST_DEV,
                    "payload": {"dev_id": dev_id, "side": "INITIATOR"},
                })
        return actions

    def _employment_application_actions(self, game_state: dict,
                                        me: dict) -> list[dict]:
        actions = []
        my_id = me.get("id")
        for dev in game_state.get("developments", []) or []:
            owner_id = dev.get("owner_id")
            if not owner_id or owner_id == my_id or dev.get("worker_id"):
                continue
            owner = self._find_player(game_state, owner_id)
            if self._is_dead_player(owner):
                continue
            if self._already_has_pending_application(me, dev):
                continue
            wage_type = self._resource_for_development_type(dev.get("type"))
            if not wage_type:
                continue
            actions.append({
                "action_command": Command.EMPLOYMENT,
                "payload": {
                    "type": "EMPLOYMENT",
                    "target_id": owner_id,
                    "dev_id": dev.get("id"),
                    "wage": dev.get("level", 1),
                    "wage_type": wage_type,
                    "is_application": True,
                },
            })
        return actions

    def _commit_work_actions(self, game_state: dict, me: dict) -> list[dict]:
        actions = []
        for job in me.get("available_work", []) or []:
            development = job.get("development", {}) or {}
            owner = self._find_player(game_state, development.get("owner_id"))
            if self._is_dead_player(owner) or development.get("is_contested"):
                continue
            actions.append({
                "action_command": Command.COMMIT_WORK,
                "payload": {"job": job},
            })
        return actions

    def _pending_employment_response_actions(self, me: dict) -> list[dict]:
        actions = []
        for action in me.get("actions", []) or []:
            if (action.get("type") == "EMPLOYMENT"
                    and action.get("status") == "PENDING"
                    and action.get("target_id") == me.get("id")):
                actions.extend(self._accept_deny(action.get("id")))
        return actions

    def _trade_actions(self, game_state: dict, me: dict,
                       memory: Memory | None) -> list[dict]:
        actions = []
        for action in me.get("actions", []) or []:
            if action.get("type") == "TRADE" and action.get("waiting_on_id") == me.get("id"):
                actions.extend(self._accept_deny(action.get("id")))
            if action.get("type") == "TRADE" and action.get("status") == "ACCEPTED":
                finalize = self._finalize_action(action, me)
                if finalize:
                    actions.append(finalize)

        actions.extend(self._draft_trade_actions(game_state, me, memory))
        return actions

    def _finalize_action(self, action: dict, me: dict) -> dict | None:
        my_id = me.get("id")
        is_initiator = action.get("initiator_id") == my_id
        already_finalized = (
            action.get("initiator_finalized", False)
            if is_initiator else action.get("target_finalized", False)
        )
        if already_finalized:
            return None

        promised = (
            action.get("offer_items") if is_initiator
            else action.get("request_items")
        ) or {}
        resources = self._resources(me)
        feasible = {}
        for resource, quantity in promised.items():
            try:
                requested = int(quantity)
            except (TypeError, ValueError):
                requested = 0
            available = int(resources.get(resource, 0) or 0)
            send_amount = max(0, min(requested, available))
            if send_amount > 0:
                feasible[resource] = send_amount

        return {
            "action_command": Command.FINALIZE,
            "payload": {
                "action_id": action.get("id"),
                "actual_items": feasible,
            },
        }

    def _draft_trade_actions(self, game_state: dict, me: dict,
                             memory: Memory | None) -> list[dict]:
        if self._already_has_outgoing_trade(me):
            return []

        resources = self._resources(me)
        trade_pairs = self._candidate_trade_pairs(resources, memory)
        if not trade_pairs:
            return []

        actions = []
        for player in self._alive_players(game_state):
            if self._trade_offers_made >= self.max_trade_offers_per_phase:
                break
            target_id = player.get("id")
            if not target_id or target_id == me.get("id"):
                continue
            if self._already_has_trade_with(me, target_id):
                continue
            for offer_resource, request_resource in trade_pairs:
                if self._trade_offers_made >= self.max_trade_offers_per_phase:
                    break
                actions.append({
                    "action_command": Command.TRADE,
                    "payload": {
                        "type": "TRADE",
                        "target_id": target_id,
                        "offer_items": {offer_resource: 1},
                        "request_items": {request_resource: 1},
                    },
                })
                self._trade_offers_made += 1
        return actions

    def _candidate_trade_pairs(self, resources: dict,
                               memory: Memory | None) -> list[tuple[str, str]]:
        offer_candidates = sorted(
            [resource for resource in RESOURCE_TYPES if self._safe_to_offer(resource, resources, memory)],
            key=lambda resource: self._offer_score(resource, resources, memory),
            reverse=True,
        )
        request_candidates = sorted(
            RESOURCE_TYPES,
            key=lambda resource: self._request_score(resource, resources, memory),
            reverse=True,
        )
        pairs = []
        for offer_resource in offer_candidates:
            for request_resource in request_candidates:
                if request_resource == offer_resource:
                    continue
                pairs.append((offer_resource, request_resource))
                if len(pairs) >= self.max_trade_offers_per_phase:
                    return pairs
        return pairs

    def _safe_to_offer(self, resource: str, resources: dict,
                       memory: Memory | None) -> bool:
        available = float(resources.get(resource, 0) or 0)
        if available <= 0:
            return False
        reserve = 1.0 if resource == "food" else 0.0
        if resource == "wood" and (memory or {}).get("fire_status") == "COLD":
            reserve = 1.0
        reserve += self._future_deficit(resource, memory)
        return available - 1.0 >= reserve

    def _night_actions(self, game_state: dict, me: dict) -> list[dict]:
        actions = []
        resources = self._resources(me)
        campfire_cost = game_state.get("campfire_cost", {"wood": 1}) or {}

        if me.get("fire_status") == "COLD" and self._is_affordable(campfire_cost, resources):
            actions.append({"action_command": Command.START_FIRE, "payload": {}})

        for action in me.get("actions", []) or []:
            if action.get("type") != "CAMPFIRE" or action.get("waiting_on_id") != me.get("id"):
                continue
            host = self._campfire_host(game_state, action)
            if host and self._has_fire_seat(game_state, host):
                actions.append({
                    "action_command": Command.ACCEPT,
                    "payload": {"action_id": action.get("id")},
                })
            actions.append({
                "action_command": Command.DENY,
                "payload": {"action_id": action.get("id")},
            })

        for player in self._alive_players(game_state):
            target_id = player.get("id")
            if not target_id or target_id == me.get("id"):
                continue
            if me.get("fire_status") == "HOST":
                actions.append({
                    "action_command": Command.CAMPFIRE,
                    "payload": {
                        "target_id": target_id,
                        "is_request": False,
                        "type": "CAMPFIRE",
                    },
                })
            elif (me.get("fire_status") == "COLD"
                  and player.get("fire_status") == "HOST"
                  and self._has_fire_seat(game_state, player)):
                actions.append({
                    "action_command": Command.CAMPFIRE,
                    "payload": {
                        "target_id": target_id,
                        "is_request": True,
                        "type": "CAMPFIRE",
                    },
                })
        return actions

    def _accept_deny(self, action_id: str | None) -> list[dict]:
        return [
            {"action_command": Command.ACCEPT, "payload": {"action_id": action_id}},
            {"action_command": Command.DENY, "payload": {"action_id": action_id}},
        ]

    def _best_request_resource(self, resources: dict, offer_resource: str | None,
                               memory: Memory | None) -> str | None:
        candidates = [resource for resource in RESOURCE_TYPES if resource != offer_resource]
        if not candidates:
            return None
        return max(candidates, key=lambda resource: self._request_score(resource, resources, memory))

    def _best_offer_resource(self, resources: dict,
                             memory: Memory | None) -> str | None:
        candidates = [resource for resource in RESOURCE_TYPES if resources.get(resource, 0) > 0]
        if not candidates:
            return None
        return max(candidates, key=lambda resource: self._offer_score(resource, resources, memory))

    def _request_score(self, resource: str, resources: dict,
                       memory: Memory | None) -> float:
        urgency = 1.0 / (float(resources.get(resource, 0) or 0) + 1.0)
        future_need = self._future_deficit(resource, memory)
        if resource == "food":
            return urgency + future_need + max(0.0, self.genome.food_desperation_weight + self.genome.food_weight)
        if resource == "wood":
            warmth_need = 1.0 if (memory or {}).get("fire_status") == "COLD" else 0.0
            return urgency + future_need + warmth_need + max(0.0, self.genome.wood_desperation_weight + self.genome.wood_weight)
        return urgency + future_need + max(0.0, self.genome.iron_desperation_weight + self.genome.iron_weight)

    def _future_deficit(self, resource: str, memory: Memory | None) -> float:
        if memory is None:
            return 0.0
        maintenance = (memory.get("maintenance_resource_deficits", {}) or {}).get(resource, 0.0) or 0.0
        upgrade = (memory.get("upgrade_resource_deficits", {}) or {}).get(resource, 0.0) or 0.0
        return float(maintenance) + float(upgrade)

    def _offer_score(self, resource: str, resources: dict,
                     memory: Memory | None) -> float:
        return float(resources.get(resource, 0) or 0) - self._request_score(resource, resources, memory)

    def _me(self, game_state: dict) -> dict:
        return game_state.get("me", {}) or {}

    def _resources(self, me: dict) -> dict:
        return me.get("resources", {"food": 0, "wood": 0, "iron": 0}) or {}

    def _map_tiles(self, game_state: dict) -> list[dict]:
        map_data = game_state.get("map", {}) or {}
        return list(map_data.values()) if isinstance(map_data, dict) else list(map_data)

    def _is_dead_player(self, player: dict | None) -> bool:
        return not player or player.get("health") == "dead"

    def _alive_players(self, game_state: dict) -> list[dict]:
        return [
            player for player in game_state.get("player_list", []) or []
            if not self._is_dead_player(player)
        ]

    def _find_player(self, game_state: dict, player_id: str | None) -> dict | None:
        return next(
            (player for player in game_state.get("player_list", []) or []
             if player.get("id") == player_id),
            None,
        )

    def _is_affordable(self, cost: dict | None, resources: dict) -> bool:
        return all(
            resources.get(resource, 0) >= amount
            for resource, amount in (cost or {}).items()
        )

    def _development_build_cost(self, tile_type: str | None,
                                game_state: dict) -> dict:
        return (game_state.get("development_costs", {}) or {}).get(
            tile_type, {}).get("build", {})

    def _upgrade_cost(self, dev: dict, game_state: dict) -> dict:
        if dev.get("upgrade_cost") is not None:
            return dev.get("upgrade_cost") or {}
        resource_costs = game_state.get("RESOURCE_COSTS", {}) or {}
        if dev.get("type") not in resource_costs:
            return {
                "food": dev.get("level", 0),
                "wood": dev.get("level", 0),
                "iron": dev.get("level", 0) * 2 + 1,
            }
        opposite = resource_costs.get(dev.get("type"))
        return {opposite: dev.get("level", 0) * 2 + 1, "iron": dev.get("level", 0)}

    def _maintenance_cost(self, dev: dict, game_state: dict) -> dict:
        if dev.get("maintenance_cost") is not None:
            return dev.get("maintenance_cost") or {}
        resource_costs = game_state.get("RESOURCE_COSTS", {}) or {}
        if dev.get("type") not in resource_costs:
            return {
                "food": dev.get("level", 0) * 2 + 1,
                "wood": dev.get("level", 0) * 2 + 1,
            }
        opposite = resource_costs.get(dev.get("type"))
        return {opposite: dev.get("level", 0), "iron": max(dev.get("level", 0) - 1, 0)}

    def _resource_for_development_type(self, dev_type: str | None) -> str | None:
        return DEVELOPMENT_RESOURCE.get(dev_type)

    def _already_has_pending_application(self, me: dict, dev: dict) -> bool:
        dev_id = dev.get("id")
        owner_id = dev.get("owner_id")
        return any(
            action.get("type") == "EMPLOYMENT"
            and action.get("dev_id") == dev_id
            and action.get("target_id") == owner_id
            and action.get("status") in [None, "PENDING", "ACCEPTED"]
            for action in me.get("actions", []) or []
        )

    def _already_has_outgoing_trade(self, me: dict) -> bool:
        return any(
            action.get("type") == "TRADE"
            and action.get("initiator_id") == me.get("id")
            and action.get("status") in ["PENDING", "NEGOTIATING", "ACCEPTED"]
            for action in me.get("actions", []) or []
        )

    def _already_has_trade_with(self, me: dict, target_id: str) -> bool:
        return any(
            action.get("type") == "TRADE"
            and target_id in [action.get("initiator_id"), action.get("target_id")]
            and action.get("status") in ["PENDING", "NEGOTIATING", "ACCEPTED"]
            for action in me.get("actions", []) or []
        )

    def _campfire_host(self, game_state: dict, action: dict) -> dict | None:
        host_id = action.get("target_id") if action.get("is_request", False) else action.get("initiator_id")
        return self._find_player(game_state, host_id)

    def _has_fire_seat(self, game_state: dict, host: dict) -> bool:
        if host.get("fire_status") != "HOST":
            return False
        max_seats = int(game_state.get("max_fire_seats", 0) or 0)
        return len(host.get("fire_guests", []) or []) < max_seats
