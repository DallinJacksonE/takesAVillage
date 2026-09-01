from service.game.packet_handling import conflict, work
from service.game.state.events import (
    DevelopmentDegraded,
    GameEnded,
    PlayerDailyNeedsConsumed,
)
from service.game.state.phase_resolution import resolve_work_phase
from service.game.state.night import build_night_locations


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

        night_locations = build_night_locations(game_state)
        previous_health = {
            player.session_id: player.health
            for player in game_state.players.values()
        }

        for player in game_state.players.values():
            game_state.apply_event(PlayerDailyNeedsConsumed(player.session_id))

        transition_visuals = {}
        for player in game_state.players.values():
            old_health = previous_health[player.session_id]
            if player.health == old_health or player.health not in {"sick", "dead"}:
                continue
            transition_visuals[player.session_id] = {
                "animation": "DEAD" if player.health == "dead" else "HURT",
                "location": night_locations[player.session_id],
            }
            game_state.notify_player(player.session_id, {
                "level": "error" if player.health == "dead" else "warning",
                "reason": "health_transition",
                "message": (
                    "You died during the night."
                    if player.health == "dead"
                    else "You became sick during the night."
                ),
            })

        if game_state.is_game_over():
            game_state.apply_event(GameEnded())
            return

        game_state.begin_night_transition(transition_visuals)

        if not game_state.night_transition:
            PhaseResolver.complete_night_cleanup(game_state)

    @staticmethod
    def complete_night_cleanup(game_state):
        game_state.contract_factory.cleanup_campfire_contracts()
        for player in game_state.players.values():
            player.cleanup_daily()
        for development in list(game_state.developments.values()):
            game_state.apply_event(DevelopmentDegraded(development.id))
        game_state.actions = []
        if game_state.is_game_over():
            game_state.apply_event(GameEnded())

    @staticmethod
    def start_day(game_state):
        work.start_work_phase(game_state)
        conflict.activate_pending_contests(game_state)
