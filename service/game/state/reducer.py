"""Authoritative state reducer for domain events."""

from service.game.state.campfire_reducer import CampfireReducer
from service.game.state.contract_reducer import ContractReducer
from service.game.state.development_reducer import DevelopmentReducer
from service.game.state.event_registry import EVENT_APPLIERS
from service.game.state.phase_reducer import PhaseReducer
from service.game.state.resource_reducer import ResourceReducer


class GameStateReducer(
        ContractReducer,
        ResourceReducer,
        DevelopmentReducer,
        PhaseReducer,
        CampfireReducer):
    def apply(self, game, event):
        game.domain_events.append(event)
        applier_name = EVENT_APPLIERS.get(type(event))
        if applier_name:
            return getattr(self, applier_name)(game, event)
        raise ValueError(f"Unsupported event: {event!r}")

    def apply_all(self, game, events):
        for event in events:
            self.apply(game, event)
