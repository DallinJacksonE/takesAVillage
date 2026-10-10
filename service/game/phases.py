from enum import Enum


class Phase(str, Enum):
    WORK = "WORK"
    TRADE = "TRADE"
    NIGHT = "NIGHT"

    @classmethod
    def value_of(cls, phase):
        return phase.value if isinstance(phase, cls) else phase
