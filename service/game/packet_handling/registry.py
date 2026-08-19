"""Central action command registry and command policies."""

from service.game.packet_handling.base import FinishPhaseCommand
from service.game.packet_handling.campfire import StartFireCommand
from service.game.packet_handling.conflict import ContestDevelopmentCommand
from service.game.packet_handling.development import (
    BuildDevelopmentCommand,
    MaintainDevelopmentCommand,
    UpgradeDevelopmentCommand,
)
from service.game.packet_handling.work import CommitWorkCommand
from service.game.packet_handling.reactions import SetEmojiCommand


COMMAND_HANDLERS = {
    "BUILD_DEV": BuildDevelopmentCommand,
    "MAINTAIN_DEV": MaintainDevelopmentCommand,
    "UPGRADE_DEV": UpgradeDevelopmentCommand,
    "CONTEST_DEV": ContestDevelopmentCommand,
    "START_FIRE": StartFireCommand,
    "COMMIT_WORK": CommitWorkCommand,
    "FINISH_PHASE": FinishPhaseCommand,
    "SET_EMOJI": SetEmojiCommand,
}

AUTO_FINISH_COMMANDS = {
    "BUILD_DEV",
    "MAINTAIN_DEV",
    "UPGRADE_DEV",
    "COMMIT_WORK",
}

PHASE_LOCK_ALLOWED_COMMANDS = {
    "FINISH_PHASE",
    "ACCEPT",
    "DENY",
    "CANCEL",
    "BARTER",
    "FINALIZE",
    "CONTEST_DEV",
    "SET_EMOJI",
}
