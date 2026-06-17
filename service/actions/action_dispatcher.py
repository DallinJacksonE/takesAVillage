from .commands import (
    BuildDevelopmentCommand, MaintainDevelopmentCommand,
    UpgradeDevelopmentCommand, ContestDevelopmentCommand,
    StartFireCommand, CommitWorkCommand, FinishPhaseCommand
)
from resolvers.social import SocialResolvers
from resolvers.conflict import ConflictResolvers
from resolvers.economy import EconomyResolvers
from logger import BackendLogger

dispatch_logger = BackendLogger("dispatcher")


class ActionDispatcher:
    COMMAND_MAP = {
        'BUILD_DEV': BuildDevelopmentCommand,
        'MAINTAIN_DEV': MaintainDevelopmentCommand,
        'UPGRADE_DEV': UpgradeDevelopmentCommand,
        'CONTEST_DEV': ContestDevelopmentCommand,
        'START_FIRE': StartFireCommand,
        'COMMIT_WORK': CommitWorkCommand,
        'FINISH_PHASE': FinishPhaseCommand
    }

    @staticmethod
    def player_can_perform_action(game_state, player, action_command) -> bool:
        if player.health == "dead":
            return False

        if (player.finished_phase and
                action_command not in ['FINISH_PHASE', 'ACCEPT',
                                       'DENY', 'CANCEL', 'BARTER',
                                       'FINALIZE']):
            dispatch_logger.warning(
                f"Player {player.session_id} already finished phase; rejecting {action_command}")
            return False
        return True

    @staticmethod
    def dispatch(game_state, user_id, data):
        if user_id is None:
            return
        player = game_state.players.get(user_id)
        if not player:
            return False

        dispatch_logger.info(f"userId: {data.get('userId')} | action: "
                             f"{data.get('action_command')} | "
                             f"payload: {data.get('payload')}")
        action_command = data.get('action_command')
        payload = data.get('payload', data)

        if not ActionDispatcher.player_can_perform_action(game_state, player, action_command):
            return False

        if action_command in ActionDispatcher.COMMAND_MAP:
            CommandClass = ActionDispatcher.COMMAND_MAP[action_command]
            command_instance = CommandClass(user_id, payload)
            success = command_instance.execute(game_state, player)

            if success and action_command in ['BUILD_DEV', 'MAINTAIN_DEV', 'UPGRADE_DEV', 'CONTEST_DEV', 'COMMIT_WORK']:
                FinishPhaseCommand(user_id, {}).execute(game_state, player)
            game_state.check_all_players_locked()
            return success

        status, contract_obj = game_state.contract_factory.process_contract(
            user_id, payload, action_command)

        if status not in ["ERROR", "ILLEGAL"]:
            if status == "UPDATED_COMPLETED" and contract_obj.type == "TRADE":
                SocialResolvers.execute_trade(game_state, contract_obj)
            elif status == "UPDATED_ACCEPTED" and contract_obj.type == "CAMPFIRE":
                SocialResolvers.seat_guest(game_state, contract_obj)

            player.add_timeline_event(
                f"ACTION_{status}",
                {"action_id": contract_obj.id,
                 "type": contract_obj.type})
            return True

        return False

    @staticmethod
    def resolve_work_phase(game_state):
        ConflictResolvers.resolve_contests(game_state)
        EconomyResolvers.resolve_work_phase(game_state)
        game_state.contract_factory.cleanup_end_of_phase()

    @staticmethod
    def resolve_night(game_state):
        game_state.add_map_hist(game_state)
        for player in game_state.players.values():
            game_state.add_player_hist(game_state, player.session_id)
        if game_state.day >= game_state.game_length:
            game_state.status = 'ENDED'
            return
        game_state.contract_factory.cleanup_campfire_contracts()
        for player in game_state.players.values():
            player.consume_daily({
                "recovery": game_state.rules.RECOVERY_RATE,
                "default": game_state.rules.DEFAULT_SICKNESS,
                "hunger_increase": game_state.rules.HUNGER_SICKNESS_INCREASE,
                "cold_increase": game_state.rules.COLD_SICKNESS_INCREASE
            })
        for dev in game_state.developments.values():
            still_exists = dev.degrade()
            if not still_exists:
                game_state.developments.pop(dev.id)
                game_state.players[dev.owner].developments.pop(dev.id)

        game_state.actions = []
        if game_state.is_game_over():
            game_state.status = "ENDED"

    @staticmethod
    def start_day(game_state):
        EconomyResolvers.start_work_phase(game_state)
