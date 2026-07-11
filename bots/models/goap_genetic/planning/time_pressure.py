from dataclasses import dataclass, field

from ..domain import Command
from ..memory import Memory


IMMEDIATE_COMMANDS = {
    Command.BUILD_DEV,
    Command.MAINTAIN_DEV,
    Command.UPGRADE_DEV,
    Command.CONTEST_DEV,
    Command.START_FIRE,
    Command.COMMIT_WORK,
    Command.ACCEPT,
    Command.DENY,
    Command.FINALIZE,
}

WAITING_COMMANDS = {
    Command.EMPLOYMENT,
    Command.TRADE,
    Command.CAMPFIRE,
}


@dataclass
class TimePressurePolicy:
    """Decides when GOAP should stop waiting for responses.

    The server exposes only remaining seconds, not the configured phase length.
    We infer the current phase's length from the largest remaining time observed
    in that phase, then reserve a proportional deadline window. Training phases
    with five seconds get roughly one second of deadline urgency; longer human
    phases naturally allow more patience before fallback actions are preferred.
    """

    deadline_fraction: float = 0.2
    minimum_deadline_seconds: float = 1.0
    _observed_phase_durations: dict[str, float] = field(default_factory=dict)

    def observe(self, memory: Memory) -> None:
        phase = memory.get("phase")
        remaining = self._remaining_seconds(memory)
        if phase is None or remaining is None:
            return
        previous = self._observed_phase_durations.get(phase, 0.0)
        self._observed_phase_durations[phase] = max(previous, remaining)

    def should_stop_waiting(self, memory: Memory) -> bool:
        if not memory.get("is_waiting"):
            return False
        return self.is_deadline_imminent(memory)

    def is_deadline_imminent(self, memory: Memory) -> bool:
        remaining = self._remaining_seconds(memory)
        if remaining is None:
            return False
        return remaining <= self._deadline_seconds(memory)

    def filter_actions(self, actions: list[dict], memory: Memory) -> list[dict]:
        if not self.is_deadline_imminent(memory):
            return actions
        immediate = [action for action in actions if self._is_immediate(action)]
        return immediate or actions

    def _is_immediate(self, action: dict) -> bool:
        command = action.get("action_command")
        if command in IMMEDIATE_COMMANDS:
            return True
        if command in WAITING_COMMANDS:
            return False
        return True

    def _deadline_seconds(self, memory: Memory) -> float:
        phase = memory.get("phase")
        observed_duration = self._observed_phase_durations.get(phase, 0.0)
        if observed_duration <= 0.0:
            observed_duration = self._remaining_seconds(memory) or 0.0
        return max(self.minimum_deadline_seconds, observed_duration * self.deadline_fraction)

    def _remaining_seconds(self, memory: Memory) -> float | None:
        raw = memory.get("time_remaining")
        if raw is None:
            return None
        try:
            return max(0.0, float(raw))
        except (TypeError, ValueError):
            return None
