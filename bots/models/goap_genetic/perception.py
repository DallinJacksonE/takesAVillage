from .memory import Memory
from .planning.development_economics import DevelopmentEconomist


class Perception:
    """
    The Sense module. Strictly a 'camera'. Parses the raw game_state JSON
    and translates it into a clean, objective Memory state.
    """

    def sense(self, game_state: dict) -> Memory:
        """
        Reads the world and returns normalized factual memory without
        preference-laden judgments.
        """
        me = game_state.get("me", {})
        my_id = me.get("id")
        resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})
        actions = me.get("actions", [])
        developments = game_state.get("developments", [])
        map_tiles = self._map_tiles(game_state.get("map", {}))
        development_costs = game_state.get("development_costs", {})

        is_waiting = any(
            action.get("type") == "EMPLOYMENT"
            and action.get("is_application")
            and action.get("initiator_id") == my_id
            and action.get("status") == "PENDING"
            for action in actions
        )

        pending_contracts = [
            action for action in actions
            if action.get("status") in ["PENDING", "ACCEPTED"]
        ]

        my_developments = []
        unowned_developments = []
        other_player_developments = []
        contested_developments = []

        for dev in developments:
            owner_id = dev.get("owner_id")
            if owner_id == my_id:
                my_developments.append(dev)
            elif not owner_id:
                unowned_developments.append(dev)
            else:
                other_player_developments.append(dev)

            if dev.get("is_contested"):
                contested_developments.append(dev)

        affordable_build_tiles = self._affordable_build_tiles(
            map_tiles, development_costs, resources)
        affordable_maintenance_developments = [
            dev for dev in my_developments
            if self._is_affordable(dev.get("maintenance_cost", {}), resources)
        ]
        affordable_upgrade_developments = [
            dev for dev in my_developments
            if self._is_affordable(dev.get("upgrade_cost", {}), resources)
        ]
        resource_production_by_dev = {
            dev.get("id"): self._resource_for_development(dev.get("type"))
            for dev in developments
            if dev.get("id")
        }

        memory = {
            # Core State
            "phase": game_state.get("phase"),
            "day": game_state.get("day"),
            "game_length": game_state.get("game_length"),
            "time_remaining": game_state.get("time_remaining"),
            "my_id": my_id,
            "health": me.get("health"),
            "sickness_chance": me.get("sickness_chance", 0.0),
            "fire_status": me.get("fire_status", "COLD"),
            "fire_guests": me.get("fire_guests", []),
            "finished_phase": me.get("finished_phase", False),
            "is_waiting": is_waiting,

            # Pure resource counts
            "food": resources.get("food", 0),
            "wood": resources.get("wood", 0),
            "iron": resources.get("iron", 0),
            "resource_total": sum(resources.get(res, 0) for res in ["food", "wood", "iron"]),

            # World facts
            "players": game_state.get("player_list", []),
            "map": game_state.get("map", {}),
            "development_costs": development_costs,
            "campfire_cost": game_state.get("campfire_cost", {}),
            "max_fire_seats": game_state.get("max_fire_seats", 0),
            "cold_sickness_rate": game_state.get("cold_sickness_rate", 0.0),
            "hunger_sickness_rate": game_state.get("hunger_sickness_rate", 0.0),
            "recovery_rate": game_state.get("recovery_rate", 0.0),
            "pending_contracts": pending_contracts,
            "available_work": me.get("available_work", []),

            # Development facts
            "my_developments": my_developments,
            "unowned_developments": unowned_developments,
            "other_player_developments": other_player_developments,
            "contested_developments": contested_developments,
            "affordable_build_tiles": affordable_build_tiles,
            "affordable_maintenance_developments": affordable_maintenance_developments,
            "affordable_upgrade_developments": affordable_upgrade_developments,
            "resource_production_by_dev": resource_production_by_dev,

            # Trade facts
            "candidate_trade_inventory": {
                "food": resources.get("food", 0),
                "wood": resources.get("wood", 0),
                "iron": resources.get("iron", 0),
            },
        }

        economist = DevelopmentEconomist()
        factual_memory = Memory(memory)
        memory.update({
            "owned_production_by_resource": economist.owned_production_by_resource(factual_memory),
            "upgrade_opportunity_value_by_resource": economist.upgrade_opportunity_value_by_resource(factual_memory),
            "maintenance_resource_deficits": economist.maintenance_required_resources(factual_memory),
            "upgrade_resource_deficits": economist.upgrade_required_resources(factual_memory),
            "at_risk_developments": economist.at_risk_developments(factual_memory),
            "upgradable_developments": economist.upgradable_developments(factual_memory),
            "workable_owned_developments": economist.workable_owned_developments(factual_memory),
        })

        return Memory(memory)

    def _map_tiles(self, map_data: dict | list) -> list[dict]:
        if isinstance(map_data, dict):
            return list(map_data.values())
        return map_data or []

    def _affordable_build_tiles(
        self,
        map_tiles: list[dict],
        development_costs: dict,
        resources: dict,
    ) -> list[dict]:
        affordable = []
        for tile in map_tiles:
            if tile.get("development"):
                continue
            build_cost = development_costs.get(tile.get("type"), {}).get("build", {})
            if self._is_affordable(build_cost, resources):
                affordable.append(tile)
        return affordable

    def _is_affordable(self, cost: dict | None, resources: dict) -> bool:
        return all(
            resources.get(resource, 0) >= amount
            for resource, amount in (cost or {}).items()
        )

    def _resource_for_development(self, development_type: str | None) -> str | None:
        if development_type is None:
            return None
        return {
            "Farm": "food",
            "Woods": "wood",
            "Mine": "iron",
        }.get(development_type)
