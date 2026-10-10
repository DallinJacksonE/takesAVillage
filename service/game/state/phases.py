"""Explicit phase-state machine for the game loop."""

from service.game.phases import Phase


class PhaseMachine:
    def __init__(self, resolver):
        self.resolver = resolver

    def advance(self, game):
        if game.phase == Phase.WORK.value:
            game._on_phase_completed(game, game.phase)
            self.resolver.resolve_work(game)
            game.start_phase(Phase.TRADE, resolver=self.resolver)
            return Phase.TRADE.value

        if game.phase == Phase.TRADE.value:
            game._on_phase_completed(game, game.phase)
            self.resolver.resolve_trade(game)
            game.start_phase(Phase.NIGHT, resolver=self.resolver)
            return Phase.NIGHT.value

        if game.phase == Phase.NIGHT.value:
            if game.night_transition:
                if not game.night_transition_ready():
                    return Phase.NIGHT.value
                complete_cleanup = getattr(self.resolver, "complete_night_cleanup", None)
                if complete_cleanup:
                    complete_cleanup(game)
                return self._complete_night(game)

            game._on_phase_completed(game, game.phase)
            self.resolver.resolve_night(game)
            if game.status == "ENDED":
                return Phase.NIGHT.value

            if game.night_transition and not game.night_transition_ready():
                return Phase.NIGHT.value

            return self._complete_night(game)

        raise ValueError(f"Unknown phase: {game.phase}")

    def _complete_night(self, game):
        if game.status == "ENDED":
            return Phase.NIGHT.value
        game.day += 1
        game.start_phase(Phase.WORK, resolver=self.resolver)
        return Phase.WORK.value
