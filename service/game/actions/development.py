import uuid

from service.game.actions.base import Command
from service.game.models.development import Development
from service.game.models.map import MapTile


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
        if not build_costs or not self._deduct_resources(
            player, build_costs
        ):
            return False

        dev_id = str(uuid.uuid4())
        new_dev = Development(
            dev_id,
            dev_type,
            player.session_id,
            game_state.rules.MAX_DEVELOPMENT_LEVEL,
            game_state.rules.MAINTENANCE_DAYS,
            game_state.rules.RESOURCE_COSTS,
        )
        game_state.developments[dev_id] = new_dev
        player.developments.append(dev_id)
        target_tile.development = new_dev
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

        if self._deduct_resources(player, dev.get_maintenance_cost()):
            dev.maintenance()
            player.add_timeline_event(
                "ACTION_COMPLETED",
                {"action": "MAINTAIN_DEV", "dev_id": dev_id},
            )
            return True
        return False


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

        if self._deduct_resources(player, dev.get_upgrade_cost()):
            dev.upgrade()
            player.add_timeline_event(
                "ACTION_COMPLETED",
                {"action": "UPGRADE_DEV", "dev_id": dev_id},
            )
            return True
        return False
