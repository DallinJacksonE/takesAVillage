import uuid
from constants import DEVELOPMENT_COSTS
from dtos import DevelopmentDTO
from models.developments import Development
from dataclasses import asdict


class EconomySystem:
    @staticmethod
    def deduct_resources(player, cost_dict):
        """Helper to check if a player can afford something, and deduct if so."""
        # 1. Check affordability
        for resource, amount in cost_dict.items():
            if player.resources.get(resource, 0) < amount:
                return False

        # 2. Deduct resources
        for resource, amount in cost_dict.items():
            player.resources[resource] -= amount

        return True

    @staticmethod
    def build_development(game_state, player, payload):
        if game_state.phase != 'WORK':
            return False

        tile_id = payload.get('tile_id')
        dev_type = payload.get('dev_type')

        if not tile_id or not dev_type:
            return False

        target_tile = next((t for t in game_state.map_data if (t.get(
            'id') if isinstance(t, dict) else getattr(t, 'id', None)) == tile_id), None)
        if not target_tile:
            return False

        existing_dev = target_tile.get('development') if isinstance(
            target_tile, dict) else getattr(target_tile, 'development', None)
        if existing_dev is not None:
            return False

        build_costs = DEVELOPMENT_COSTS.get(dev_type, {}).get("build", {})
        if not build_costs or not EconomySystem.deduct_resources(player, build_costs):
            return False

        dev_id = str(uuid.uuid4())
        new_dev = Development(
            dev_id=dev_id, dev_type=dev_type, dev_owner=player.session_id)

        game_state.developments[dev_id] = new_dev
        dev_dto = DevelopmentDTO.from_model(new_dev)

        if isinstance(target_tile, dict):
            target_tile['development'] = asdict(dev_dto)
        else:
            target_tile.development = dev_dto

        player.add_timeline_event("ACTION_COMPLETED", {
                                  "action": "BUILD_DEV", "dev_id": dev_id, "type": dev_type})
        return True

    @staticmethod
    def maintain_development(game_state, player, payload):
        """Allows any player to pay the maintenance cost to restore a development's days."""
        dev_id = payload.get('dev_id')
        dev = game_state.developments.get(dev_id)

        if not dev:
            return False

        maintain_cost = DEVELOPMENT_COSTS.get(dev.type, {}).get("maintain", {})
        if EconomySystem.deduct_resources(player, maintain_cost):
            dev.maintenence_days = 7  # Restoring to max days
            player.add_timeline_event(
                "ACTION_COMPLETED", {"action": "MAINTAIN_DEV", "dev_id": dev_id})
            return True

        return False

    @staticmethod
    def upgrade_development(game_state, player, payload):
        """Allows any player to pay the upgrade cost to increase a development's level."""
        dev_id = payload.get('dev_id')
        dev = game_state.developments.get(dev_id)

        if not dev or dev.level >= 3:
            return False

        upgrade_cost = DEVELOPMENT_COSTS.get(dev.type, {}).get("upgrade", {})
        if EconomySystem.deduct_resources(player, upgrade_cost):
            dev.upgrade()
            player.add_timeline_event(
                "ACTION_COMPLETED", {"action": "UPGRADE_DEV", "dev_id": dev_id})
            return True

        return False

    @staticmethod
    def resolve_work_phase(game_state):
        """Calculates yields and forces employment wage transfers."""
        DEV_OUTPUT_MAP = {"Farm": "food", "Woods": "wood", "Mine": "iron"}

        for player in game_state.players.values():
            ca = getattr(player, 'committed_action', None)

            if ca and isinstance(ca, dict):
                dev_data = ca.get('development', {})
                owner_id = dev_data.get('owner_id')
                dev_type = dev_data.get('type')
                dev_level = int(dev_data.get('level', 1))

                # Employment Details
                wage = int(ca.get('wage', 0))
                wage_type = ca.get('wage_type', 'food')
                is_working_for_other = (owner_id != player.session_id)

                owner = game_state.players.get(owner_id)
                resource_produced = DEV_OUTPUT_MAP.get(dev_type)

                if owner and resource_produced:
                    # 1. Base Yield Generation (Owner gets the output)
                    owner.resources[resource_produced] = owner.resources.get(
                        resource_produced, 0) + dev_level

                    # 2. Wage Transfer Logic (If employed by someone else)
                    if is_working_for_other and wage > 0:
                        # Ensure owner's balance doesn't go below 0 (system forces debt/bankruptcy to 0 for now)
                        actual_wage = min(
                            wage, owner.resources.get(wage_type, 0))

                        owner.resources[wage_type] -= actual_wage
                        player.resources[wage_type] = player.resources.get(
                            wage_type, 0) + actual_wage

                        player.add_timeline_event("WAGE_RECEIVED", {
                                                  "amount": actual_wage, "type": wage_type, "employer": owner_id})
                        owner.add_timeline_event("WAGE_PAID", {
                                                 "amount": actual_wage, "type": wage_type, "employee": player.session_id})

            # Clean up the phase state for the next day
            player.committed_action = None
            player.reset_phase()
