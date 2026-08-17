"""Deterministic phase-resolution ordering.

Phase resolvers should keep the high-level order here instead of scattering
implicit sequencing across call sites. This is intentionally small for now:
it documents and centralizes the WORK phase ordering that protects deferred
intents from rollback-style mutation bugs.
"""

from service.game.packet_handling import conflict, work


WORK_RESOLUTION_ORDER = (
    "resolve_development_intents",
    "resolve_work_intents",
    "resolve_contests",
    "cleanup_contracts",
)


def resolve_work_phase(game_state):
    """Resolve the WORK phase in the authoritative deterministic order."""
    work.resolve_work_phase(game_state)
    conflict.resolve_contests(game_state)
    game_state.contract_factory.cleanup_end_of_phase()
