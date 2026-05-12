import uuid
from dataclasses import asdict
from models.developments import Development
from dtos import DevelopmentDTO

# ==========================================
# BASE COMMAND
# ==========================================


class Command:
    def __init__(self, initiator_id, payload):
        self.initiator_id = initiator_id
        self.payload = payload

    def execute(self, game_state, player) -> bool:
        raise NotImplementedError(
            "Each command must define its own execute method.")

    def _deduct_resources(self, player, cost_dict) -> bool:
        """Shared helper for checking and deducting resource costs."""
        for resource, amount in cost_dict.items():
            if player.resources.get(resource, 0) < amount:
                return False
        for resource, amount in cost_dict.items():
            player.resources[resource] -= amount
        return True

# ==========================================
# ECONOMY COMMANDS
# ==========================================


class BuildDevelopmentCommand(Command):
    def execute(self, game_state, player):
        if game_state.phase != 'WORK':
            return False

        tile_id = self.payload.get('tile_id')
        target_tile = game_state.map_data.get(tile_id)
        if not target_tile or not tile_id:
            print("No tile or id found")
            return False
        dev_type = target_tile.type
        print("dev type: ", dev_type)

        if not tile_id or not dev_type:
            return False

        existing_dev = target_tile.get('development') if isinstance(
            target_tile, dict) else getattr(target_tile, 'development', None)
        if existing_dev is not None:
            print("build failed, existing_dev is not None")
            return False

        build_costs = game_state.development_costs.get(
            dev_type, {}).get("build", {})
        if not build_costs or not self._deduct_resources(player, build_costs):
            print("Build failed, insufficent resources")
            return False

        dev_id = str(uuid.uuid4())
        new_dev = Development(
            dev_id=dev_id, dev_type=dev_type, dev_owner=player.session_id)

        game_state.developments[dev_id] = new_dev

        target_tile.development = new_dev
        target_tile.owner_id = player.session_id
        player.add_timeline_event("ACTION_COMPLETED", {
                                  "action": "BUILD_DEV",
                                  "dev_id": dev_id,
                                  "type": dev_type})
        return True


class MaintainDevelopmentCommand(Command):
    def execute(self, game_state, player):
        dev_id = self.payload.get('dev_id')
        dev = game_state.developments.get(dev_id)

        if not dev:
            return False

        maintain_cost = game_state.development_costs.get(
            dev.type, {}).get("maintain", {})
        if self._deduct_resources(player, maintain_cost):
            dev.maintenence_days = 7
            player.add_timeline_event(
                "ACTION_COMPLETED", {"action": "MAINTAIN_DEV", "dev_id": dev_id})
            return True
        return False


class UpgradeDevelopmentCommand(Command):
    def execute(self, game_state, player):
        dev_id = self.payload.get('dev_id')
        dev = game_state.developments.get(dev_id)

        if not dev or dev.level >= 3:
            return False

        upgrade_cost = game_state.development_costs.get(
            dev.type, {}).get("upgrade", {})
        if self._deduct_resources(player, upgrade_cost):
            dev.upgrade()
            player.add_timeline_event(
                "ACTION_COMPLETED", {"action": "UPGRADE_DEV", "dev_id": dev_id})
            return True
        return False

# ==========================================
# CONFLICT COMMAND
# ==========================================


class ContestDevelopmentCommand(Command):
    def execute(self, game_state, player):
        if game_state.phase != 'WORK':
            return False

        dev_id = self.payload.get('dev_id')
        side = self.payload.get('side')  # 'INITIATOR', 'CONTESTER', 'OWNER'
        dev = game_state.developments.get(dev_id)

        if not dev:
            return False

        if side == 'INITIATOR':
            if dev.is_contested or dev.owner == player.session_id:
                return False
            dev.contester_id = player.session_id

        player.committed_action = {
            "type": "CONTEST_ACTION",
            "dev_id": dev_id,
            "side": 'CONTESTER' if side == 'INITIATOR' else side
        }

        player.add_timeline_event(
            "ACTION_COMPLETED", {"action": "CONTEST", "dev_id": dev_id, "side": side})
        return True

# ==========================================
# SOCIAL COMMANDS
# ==========================================


class StartFireCommand(Command):
    def execute(self, game_state, player):
        if game_state.phase != 'NIGHT' or player.fire_status == "HOST":
            return False

        cost = game_state.campfire_cost.get("wood", 1)
        if self._deduct_resources(player, {"wood": cost}):
            player.fire_status = "HOST"
            player.fire_guests = []
            player.add_timeline_event(
                "ACTION_COMPLETED", {"action": "START_FIRE"})
            return True
        return False

# ==========================================
# GAME/PHASE FLOW COMMANDS
# ==========================================


class CommitWorkCommand(Command):
    def execute(self, game_state, player):
        work_action = self.payload.get('work_action')
        if not work_action:
            return False

        dev_id = work_action.get('development', {}).get('id')
        live_dev = game_state.developments.get(dev_id)

        # Stop work if property is currently under active hold
        if live_dev and getattr(live_dev, 'is_contested', False):
            return False

        player.committed_action = work_action

        # Handle accepted job contract cleanup
        action_id = work_action.get('action_id')
        if action_id:
            chosen_action = game_state.contract_factory.find_contract(
                action_id)
            if chosen_action:
                chosen_action.status = 'COMPLETED'

            for act in list(player.actions.values()):
                if act.type == 'EMPLOYMENT' and act.status == 'ACCEPTED' and act.id != action_id:
                    act.status = 'CANCELED'

        return True


class FinishPhaseCommand(Command):
    def execute(self, game_state, player):
        player.finished_phase = True
        game_state.check_all_players_locked()
        return True
