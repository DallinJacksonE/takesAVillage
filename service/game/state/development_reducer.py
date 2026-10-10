"""Development event appliers for the game-state reducer."""

from service.game.models.development import Development
from service.game.state.events import DevelopmentDestroyed


class DevelopmentReducer:
    def _apply_development_built(self, game, event):
        tile = game.map_data[event.tile_id]
        development = Development(
            event.development_id,
            event.development_type,
            event.owner_id,
            game.rules.MAX_DEVELOPMENT_LEVEL,
            game.rules.MAINTENANCE_DAYS,
            game.rules.RESOURCE_COSTS,
        )
        tile.development = development
        owner = game.players[event.owner_id]
        if development.id not in owner.developments:
            owner.developments.append(development.id)
        return development

    def _apply_development_degraded(self, game, event):
        development = game.developments[event.development_id]
        if not development.degrade():
            self.apply(game, DevelopmentDestroyed(
                development.id,
                development.owner,
            ))
        return development

    def _apply_development_destroyed(self, game, event):
        game.developments.pop(event.development_id, None)
        owner = game.players.get(event.owner_id)
        if owner and event.development_id in owner.developments:
            owner.developments.remove(event.development_id)
        return event.development_id

    def _apply_development_maintained(self, game, event):
        development = game.developments[event.development_id]
        development.maintenance()
        return development

    def _apply_development_upgraded(self, game, event):
        development = game.developments[event.development_id]
        development.upgrade()
        return development

    def _apply_development_contest_activated(self, game, event):
        development = game.developments[event.development_id]
        development.is_contested = True
        development.pending_contest = False
        development.pending_contest_day = None
        development.contest_initiator_id = event.initiator_id
        development.contester_supporters = []
        development.owner_supporters = []
        game.contest_count += 1
        return development

    def _apply_development_ownership_transferred(self, game, event):
        development = game.developments[event.development_id]
        old_owner = game.players.get(event.old_owner_id)
        new_owner = game.players.get(event.new_owner_id)
        if old_owner and development.id in old_owner.developments:
            old_owner.developments.remove(development.id)
        if new_owner and development.id not in new_owner.developments:
            new_owner.developments.append(development.id)
        development.owner = event.new_owner_id
        return development

    def _apply_development_contest_cleared(self, game, event):
        development = game.developments[event.development_id]
        development.is_contested = False
        development.contest_initiator_id = None
        development.contester_supporters = []
        development.owner_supporters = []
        return development
