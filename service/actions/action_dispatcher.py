from .commands import (
    BuildDevelopmentCommand, MaintainDevelopmentCommand,
    UpgradeDevelopmentCommand, ContestDevelopmentCommand,
    StartFireCommand, CommitWorkCommand, FinishPhaseCommand
)
from resolvers.social import SocialResolvers
from resolvers.conflict import ConflictResolvers
from resolvers.economy import EconomyResolvers


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
    def dispatch(game_state, user_id, data):
        player = game_state.players.get(user_id)
        if not player:
            return False

        action_command = data.get('action_command') or data.get(
            'actionId') or data.get('actionCommand')
        payload = data.get('payload', data)

        if player.finished_phase and action_command != 'FINISH_PHASE':
            return False

        # 1. Execute Instant Commands
        if action_command in ActionDispatcher.COMMAND_MAP:
            CommandClass = ActionDispatcher.COMMAND_MAP[action_command]
            command_instance = CommandClass(user_id, payload)

            success = command_instance.execute(game_state, player)

            # Auto-finish phase for certain actions
            if success and action_command in ['BUILD_DEV', 'MAINTAIN_DEV',
                                              'UPGRADE_DEV', 'CONTEST_DEV',
                                              'COMMIT_WORK']:
                FinishPhaseCommand(user_id, {}).execute(game_state, player)

            return success

        # 2. Route Contract/Drafting Actions
        status, contract_obj = game_state.contract_factory.process_contract(
            user_id, payload, action_command)

        if status not in ["ERROR", "ILLEGAL"]:
            # Real-time Contract Intercepts using new Resolvers
            if status == "UPDATED_COMPLETED" and contract_obj.type == "TRADE":
                SocialResolvers.execute_trade(game_state, contract_obj)
            elif status == "UPDATED_ACCEPTED" and contract_obj.type == "CAMPFIRE":
                host = game_state.players.get(contract_obj.target_id)
                if host:
                    SocialResolvers.seat_guest(game_state, host, contract_obj)

            player.add_timeline_event(
                f"ACTION_{status}", {"action_id": contract_obj.id,
                                     "type": contract_obj.type})
            return True

        return False

    @staticmethod
    def resolve_work_phase(game_state):
        ConflictResolvers.resolve_contests(game_state)
        EconomyResolvers.resolve_work_phase(game_state)
