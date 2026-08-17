from service.game.packet_handling.contracts import execute_trade
from service.game.packet_handling.base import FinishPhaseCommand
from service.game.packet_handling.phase_resolution import PhaseResolver
from service.game.packet_handling.registry import (
    AUTO_FINISH_COMMANDS,
    COMMAND_HANDLERS,
    PHASE_LOCK_ALLOWED_COMMANDS,
)
from service.logging import BackendLogger


dispatch_logger = BackendLogger("dispatcher")


class PacketDispatcher:
    COMMAND_MAP = COMMAND_HANDLERS

    @staticmethod
    def player_can_perform_action(game_state, player, action_command) -> bool:
        if player.health == "dead":
            return False
        if (
            player.finished_phase
            and action_command not in PHASE_LOCK_ALLOWED_COMMANDS
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

        if not PacketDispatcher.player_can_perform_action(
            game_state, player, action_command
        ):
            return False

        if action_command in PacketDispatcher.COMMAND_MAP:
            command_class = PacketDispatcher.COMMAND_MAP[action_command]
            success = command_class(user_id, payload).execute(
                game_state, player
            )
            if success and action_command in AUTO_FINISH_COMMANDS:
                FinishPhaseCommand(user_id, {}).execute(
                    game_state, player
                )
            game_state.check_all_players_locked()
            return success

        status, contract = game_state.contract_factory.process_contract(
            user_id, payload, action_command
        )
        if status not in ["ERROR", "ILLEGAL"] and contract is not None:
            if status == "UPDATED_FINALIZED" and contract.type == "TRADE":
                execute_trade(game_state, contract)
            player.add_timeline_event(
                f"ACTION_{status}",
                {"action_id": contract.id, "type": contract.type},
            )
            return True
        return False

    resolve_work_phase = staticmethod(PhaseResolver.resolve_work)
    resolve_night = staticmethod(PhaseResolver.resolve_night)
    start_day = staticmethod(PhaseResolver.start_day)
