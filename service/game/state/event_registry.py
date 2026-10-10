"""Registry of domain event types to reducer applier methods.

This module is the state layer's event dispatch table. Command/action code emits
instances from ``service.game.state.events``; the reducer looks up each event
class here and invokes the corresponding mutation method.
"""

from service.game.state.events import (
    ContractCreated,
    ContractExpired,
    ContractRemoved,
    ContractUpdated,
    DevelopmentBuilt,
    DevelopmentContestActivated,
    DevelopmentContestCleared,
    DevelopmentDegraded,
    DevelopmentDestroyed,
    DevelopmentMaintained,
    DevelopmentOwnershipTransferred,
    DevelopmentUpgraded,
    EmploymentAccepted,
    FireStarted,
    GameEnded,
    GuestSeatedAtFire,
    PlayerDailyNeedsConsumed,
    PlayerPhaseResolved,
    PlayerResourcesGained,
    PlayerResourcesSpent,
    PlayerResourcesTransferred,
    TradeFinalized,
)


EVENT_APPLIERS = {
    ContractCreated: "_apply_contract_created",
    ContractUpdated: "_apply_contract_updated",
    ContractRemoved: "_apply_contract_removed",
    ContractExpired: "_apply_contract_expired",
    TradeFinalized: "_apply_trade_finalized",
    EmploymentAccepted: "_apply_employment_accepted",
    PlayerPhaseResolved: "_apply_player_phase_resolved",
    PlayerResourcesSpent: "_apply_resources_spent",
    PlayerResourcesGained: "_apply_resources_gained",
    PlayerResourcesTransferred: "_apply_resources_transferred",
    DevelopmentBuilt: "_apply_development_built",
    PlayerDailyNeedsConsumed: "_apply_player_daily_needs_consumed",
    DevelopmentDegraded: "_apply_development_degraded",
    DevelopmentDestroyed: "_apply_development_destroyed",
    GameEnded: "_apply_game_ended",
    DevelopmentMaintained: "_apply_development_maintained",
    DevelopmentUpgraded: "_apply_development_upgraded",
    DevelopmentContestActivated: "_apply_development_contest_activated",
    DevelopmentOwnershipTransferred: "_apply_development_ownership_transferred",
    DevelopmentContestCleared: "_apply_development_contest_cleared",
    FireStarted: "_apply_fire_started",
    GuestSeatedAtFire: "_apply_guest_seated_at_fire",
}
