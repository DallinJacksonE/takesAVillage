from service.game.packet_handling import conflict, work
from service.game.state.events import (
    DevelopmentDegraded,
    GameEnded,
    PlayerDailyNeedsConsumed,
)
from service.game.state.phase_resolution import resolve_work_phase


class PhaseResolver:
    @staticmethod
    def resolve_work(game_state):
        resolve_work_phase(game_state)

    @staticmethod
    def resolve_trade(game_state):
        if game_state.training:
            return
        for player in game_state.players.values():
            player.old_history = player.trade_history.copy()
            player.trade_history = []

    @staticmethod
    def resolve_night(game_state):
        game_state.add_map_hist(game_state)
        for player in game_state.players.values():
            game_state.add_player_hist(game_state, player.session_id)

        if game_state.day >= game_state.game_length:
            game_state.apply_event(GameEnded())
            return

        game_state.contract_factory.cleanup_campfire_contracts()
        for player in game_state.players.values():
            game_state.apply_event(PlayerDailyNeedsConsumed(player.session_id))

        for development in list(game_state.developments.values()):
            game_state.apply_event(DevelopmentDegraded(development.id))

        game_state.actions = []
        if game_state.is_game_over():
            game_state.apply_event(GameEnded())

    @staticmethod
    def start_day(game_state):
        work.start_work_phase(game_state)
        conflict.activate_pending_contests(game_state)
