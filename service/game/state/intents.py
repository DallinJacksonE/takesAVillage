"""Phase intent records for simultaneous game resolution."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkIntent:
    player_id: str
    development_id: str
    job: dict

    @property
    def committed_action(self):
        return self.job


@dataclass(frozen=True)
class UpgradeIntent:
    player_id: str
    development_id: str

    @property
    def committed_action(self):
        return {
            "type": "UPGRADE_DEV",
            "dev_id": self.development_id,
        }


@dataclass(frozen=True)
class MaintainIntent:
    player_id: str
    development_id: str

    @property
    def committed_action(self):
        return {
            "type": "MAINTAIN_DEV",
            "dev_id": self.development_id,
        }


@dataclass(frozen=True)
class ContestIntent:
    player_id: str
    development_id: str
    side: str

    @property
    def committed_action(self):
        return {
            "type": "CONTEST_ACTION",
            "dev_id": self.development_id,
            "side": self.side,
        }
