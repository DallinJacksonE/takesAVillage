"""Domain events emitted by accepted game commands/resolvers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerResourcesSpent:
    player_id: str
    resources: dict


@dataclass(frozen=True)
class PlayerResourcesGained:
    player_id: str
    resources: dict


@dataclass(frozen=True)
class PlayerResourcesTransferred:
    from_player_id: str
    to_player_id: str
    resources: dict


@dataclass(frozen=True)
class PlayerPhaseResolved:
    player_id: str


@dataclass(frozen=True)
class ContractUpdated:
    contract: object


@dataclass(frozen=True)
class ContractCreated:
    contract: object


@dataclass(frozen=True)
class ContractRemoved:
    contract_id: str


@dataclass(frozen=True)
class ContractExpired:
    contract_id: str


@dataclass(frozen=True)
class TradeFinalized:
    contract_id: str
    initiator_lied: bool = False
    target_lied: bool = False


@dataclass(frozen=True)
class EmploymentAccepted:
    contract_id: str
    employer_id: str
    worker_id: str
    development_id: str
    wage: int
    wage_type: str


@dataclass(frozen=True)
class DevelopmentBuilt:
    development_id: str
    tile_id: str
    owner_id: str
    development_type: str


@dataclass(frozen=True)
class PlayerDailyNeedsConsumed:
    player_id: str


@dataclass(frozen=True)
class DevelopmentDegraded:
    development_id: str


@dataclass(frozen=True)
class DevelopmentDestroyed:
    development_id: str
    owner_id: str


@dataclass(frozen=True)
class GameEnded:
    pass


@dataclass(frozen=True)
class DevelopmentMaintained:
    development_id: str


@dataclass(frozen=True)
class DevelopmentUpgraded:
    development_id: str


@dataclass(frozen=True)
class DevelopmentContestActivated:
    development_id: str
    initiator_id: str


@dataclass(frozen=True)
class DevelopmentContestCleared:
    development_id: str


@dataclass(frozen=True)
class DevelopmentOwnershipTransferred:
    development_id: str
    old_owner_id: str
    new_owner_id: str


@dataclass(frozen=True)
class FireStarted:
    player_id: str


@dataclass(frozen=True)
class GuestSeatedAtFire:
    contract_id: str
    host_id: str
    guest_id: str
