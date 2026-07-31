from service.game.actions.base import FinishPhaseCommand
from service.game.actions.campfire import StartFireCommand, seat_guest
from service.game.actions.conflict import ContestDevelopmentCommand
from service.game.actions.contracts import execute_trade
from service.game.actions.development import (
    BuildDevelopmentCommand,
    MaintainDevelopmentCommand,
    UpgradeDevelopmentCommand,
)
from service.game.actions.phase_resolution import PhaseResolver
from service.game.actions.work import CommitWorkCommand
from service.logging import BackendLogger


dispatch_logger = BackendLogger("dispatcher")


class ActionDispatcher:
    COMMAND_MAP = {
        "BUILD_DEV": BuildDevelopmentCommand,
        "MAINTAIN_DEV": MaintainDevelopmentCommand,
        "UPGRADE_DEV": UpgradeDevelopmentCommand,
        "CONTEST_DEV": ContestDevelopmentCommand,
        "START_FIRE": StartFireCommand,
        "COMMIT_WORK": CommitWorkCommand,
        "FINISH_PHASE": FinishPhaseCommand,
    }

    @staticmethod
    def player_can_perform_action(game_state, player, action_command) -> bool:
        if player.health == "dead":
            return False
        if (
            player.finished_phase
            and action_command
            not in [
                "FINISH_PHASE",
                "ACCEPT",
                "DENY",
                "CANCEL",
                "BARTER",
                "FINALIZE",
            ]
        ):
            dispatch_logger.warning(
                f"Player {player.session_id} already finished phase; "
                f"rejecting {action_command}"
            )
            return False
        return True

    @staticmethod
    def dispatch(game_state, user_id, data):
        if user_id is None:
            return None
        player = game_state.players.get(user_id)
        if not player:
            return False

        action_command = data.get("action_command")
        payload = data.get("payload", data)
        dispatch_logger.info(
            f"user_id: {user_id} | action: {action_command} | "
            f"payload: {payload}"
        )

        if not ActionDispatcher.player_can_perform_action(
            game_state, player, action_command
        ):
            return False

        if action_command in ActionDispatcher.COMMAND_MAP:
            command_class = ActionDispatcher.COMMAND_MAP[action_command]
            success = command_class(user_id, payload).execute(
                game_state, player
            )
            if success and action_command in [
                "BUILD_DEV",
                "MAINTAIN_DEV",
                "UPGRADE_DEV",
                "CONTEST_DEV",
                "COMMIT_WORK",
            ]:
                FinishPhaseCommand(user_id, {}).execute(
                    game_state, player
                )
            game_state.check_all_players_locked()
            return success

        status, contract = game_state.contract_factory.process_contract(
            user_id, payload, action_command
        )
        if status not in ["ERROR", "ILLEGAL"] and contract is not None:
            if status == "UPDATED_COMPLETED" and contract.type == "TRADE":
                execute_trade(game_state, contract)
            elif (
                status == "UPDATED_ACCEPTED"
                and contract.type == "CAMPFIRE"
            ):
                seat_guest(game_state, contract)

            player.add_timeline_event(
                f"ACTION_{status}",
                {"action_id": contract.id, "type": contract.type},
            )
            return True
        return False

    resolve_work_phase = staticmethod(PhaseResolver.resolve_work)
    resolve_night = staticmethod(PhaseResolver.resolve_night)
    start_day = staticmethod(PhaseResolver.start_day)
