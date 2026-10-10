"""Resource event appliers for the game-state reducer."""


class ResourceReducer:
    def _apply_resources_spent(self, game, event):
        player = game.players[event.player_id]
        for resource, amount in event.resources.items():
            player.resources[resource] -= amount

    def _apply_resources_gained(self, game, event):
        player = game.players[event.player_id]
        for resource, amount in event.resources.items():
            player.resources[resource] = (
                player.resources.get(resource, 0) + amount
            )

    def _apply_resources_transferred(self, game, event):
        source = game.players[event.from_player_id]
        target = game.players[event.to_player_id]
        for resource, amount in event.resources.items():
            source.resources[resource] -= amount
            target.resources[resource] = (
                target.resources.get(resource, 0) + amount
            )
