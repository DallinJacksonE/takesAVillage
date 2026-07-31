class Command:
    def __init__(self, initiator_id, payload):
        self.initiator_id = initiator_id
        self.payload = payload

    def execute(self, game_state, player) -> bool:
        raise NotImplementedError(
            "Each command must define its own execute method."
        )

    def _deduct_resources(self, player, cost_dict) -> bool:
        for resource, amount in cost_dict.items():
            if player.resources.get(resource, 0) < amount:
                return False
        for resource, amount in cost_dict.items():
            player.resources[resource] -= amount
        return True


class FinishPhaseCommand(Command):
    def execute(self, game_state, player):
        player.finished_phase = True
        game_state.check_all_players_locked()
        return True
