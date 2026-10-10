"""Pure contract state transition guards."""

from dataclasses import dataclass


TERMINAL_STATUSES = {"FINALIZED", "DENIED", "EXPIRED"}
WAITING_COMMANDS = {"ACCEPT", "DENY", "BARTER"}
PARTY_COMMANDS = WAITING_COMMANDS | {"CANCEL", "FINALIZE"}


@dataclass(frozen=True)
class ContractTransition:
    allowed: bool
    reason: str | None = None

    def __bool__(self):
        return self.allowed


def validate_contract_transition(contract, user_id, action_command):
    if action_command not in PARTY_COMMANDS:
        return ContractTransition(False, "UNKNOWN_COMMAND")

    if user_id not in {contract.initiator_id, contract.target_id}:
        return ContractTransition(False, "NOT_CONTRACT_PARTY")

    if contract.status in TERMINAL_STATUSES:
        return ContractTransition(False, "TERMINAL_CONTRACT")

    if action_command in WAITING_COMMANDS:
        if contract.status != "PENDING":
            return ContractTransition(False, "CONTRACT_NOT_PENDING")
        if contract.waiting_on_id != user_id:
            return ContractTransition(False, "WAITING_ON_OTHER_PLAYER")
        return ContractTransition(True)

    if action_command == "CANCEL":
        if contract.status != "PENDING":
            return ContractTransition(False, "CONTRACT_NOT_PENDING")
        if user_id != contract.initiator_id:
            return ContractTransition(False, "ONLY_INITIATOR_CAN_CANCEL")
        return ContractTransition(True)

    if action_command == "FINALIZE":
        if contract.status != "ACCEPTED":
            return ContractTransition(False, "CONTRACT_NOT_ACCEPTED")
        return ContractTransition(True)

    return ContractTransition(False, "UNKNOWN_COMMAND")
