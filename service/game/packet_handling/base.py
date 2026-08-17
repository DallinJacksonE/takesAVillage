from service.game.state.events import PlayerPhaseResolved


class Command:
    def __init__(self, initiator_id, payload):
        self.initiator_id = initiator_id
        self.payload = payload

    def execute(self, game_state, player) -> bool:
        raise NotImplementedError(
            "Each command must define its own execute method."
        )

class FinishPhaseCommand(Command):
    def execute(self, game_state, player):
        game_state.apply_event(PlayerPhaseResolved(player.session_id))
        game_state.check_all_players_locked()
        return True
