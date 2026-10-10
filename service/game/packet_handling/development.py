import uuid

from service.game.packet_handling.base import Command
from service.game.models.map import MapTile
from service.game.state.events import (
    DevelopmentBuilt,
    PlayerResourcesSpent,
)
from service.game.state.intents import MaintainIntent, UpgradeIntent


class BuildDevelopmentCommand(Command):
    def execute(self, game_state, player):
        if game_state.phase != "WORK":
            return False

        tile_id = self.payload.get("tile_id")
        target_tile: MapTile = game_state.map_data.get(tile_id)
        if not target_tile or not tile_id:
            return False
        dev_type = target_tile.type
        if not dev_type:
            return False

        existing_dev = (
            target_tile.get("development")
            if isinstance(target_tile, dict)
            else getattr(target_tile, "development", None)
        )
        if existing_dev is not None:
            return False

        build_costs = game_state.development_costs.get(
            dev_type, {}
        ).get("build", {})
        if not build_costs:
            return False
        if any(
            player.resources.get(resource, 0) < amount
            for resource, amount in build_costs.items()
        ):
            return False

        dev_id = str(uuid.uuid4())
        game_state.apply_events([
            PlayerResourcesSpent(player.session_id, build_costs.copy()),
            DevelopmentBuilt(
                dev_id, tile_id, player.session_id, dev_type),
        ])
        player.add_timeline_event(
            "ACTION_COMPLETED",
            {"action": "BUILD_DEV", "dev_id": dev_id, "type": dev_type},
        )
        player.committed_action = {
            "Action": "Build",
            "Type": dev_type,
            "Tile_Id": tile_id,
        }
        return True


class MaintainDevelopmentCommand(Command):
    def execute(self, game_state, player):
        if game_state.phase != "WORK":
            return False
        dev_id = self.payload.get("dev_id")
        dev = game_state.developments.get(dev_id)
        if not dev or dev.owner != player.session_id:
            return False

        maintenance_cost = dev.get_maintenance_cost()
        if any(
            player.resources.get(resource, 0) < amount
            for resource, amount in maintenance_cost.items()
        ):
            return False
        game_state.set_intent(MaintainIntent(player.session_id, dev_id))
        player.add_timeline_event(
            "ACTION_INTENT_SUBMITTED",
            {"action": "MAINTAIN_DEV", "dev_id": dev_id},
        )
        return True


class UpgradeDevelopmentCommand(Command):
    def execute(self, game_state, player):
        if game_state.phase != "WORK":
            return False
        dev_id = self.payload.get("dev_id")
        dev = game_state.developments.get(dev_id)
        if (not dev
                or dev.owner != player.session_id
                or not dev.can_upgrade):
            return False

        upgrade_cost = dev.get_upgrade_cost()
        if any(
            player.resources.get(resource, 0) < amount
            for resource, amount in upgrade_cost.items()
        ):
            return False

        game_state.set_intent(UpgradeIntent(player.session_id, dev_id))
        player.add_timeline_event(
            "ACTION_INTENT_SUBMITTED",
            {"action": "UPGRADE_DEV", "dev_id": dev_id},
        )
        return True
