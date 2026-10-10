"""Phase/lifecycle event appliers for the game-state reducer."""


class PhaseReducer:
    def _apply_player_phase_resolved(self, game, event):
        player = game.players[event.player_id]
        player.resolve_phase()
        return player

    def _apply_player_daily_needs_consumed(self, game, event):
        player = game.players[event.player_id]
        player.consume_daily({
            "recovery": game.rules.RECOVERY_RATE,
            "default": game.rules.DEFAULT_SICKNESS,
            "hunger_increase": game.rules.HUNGER_SICKNESS_INCREASE,
            "cold_increase": game.rules.COLD_SICKNESS_INCREASE,
        })
        return player

    def _apply_game_ended(self, game, event):
        game.status = "ENDED"
        return game
