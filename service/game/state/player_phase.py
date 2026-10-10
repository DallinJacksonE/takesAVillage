"""Explicit per-player phase-state values.

``finished_phase`` remains a compatibility projection for clients/tests that
still speak in terms of a boolean lock. New state-transition code should use
``phase_state`` values instead.
"""

from enum import Enum


class PlayerPhaseState(str, Enum):
    ACTIVE = "ACTIVE"
    INTENT_SUBMITTED = "INTENT_SUBMITTED"
    NEEDS_REPLACEMENT = "NEEDS_REPLACEMENT"
    RESOLVED = "RESOLVED"
    DEAD = "DEAD"


LOCKED_PHASE_STATES = {
    PlayerPhaseState.INTENT_SUBMITTED.value,
    PlayerPhaseState.RESOLVED.value,
    PlayerPhaseState.DEAD.value,
}
