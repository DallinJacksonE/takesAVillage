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
            game._on_phase_completed(game, game.phase)
            self.resolver.resolve_night(game)

            if game.status == "ENDED":
                return Phase.NIGHT.value

            game.day += 1
            game.start_phase(Phase.WORK, resolver=self.resolver)
            return Phase.WORK.value

        raise ValueError(f"Unknown phase: {game.phase}")