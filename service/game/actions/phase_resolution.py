from service.game.actions import conflict, work


class PhaseResolver:
    @staticmethod
    def resolve_work(game_state):
        conflict.resolve_contests(game_state)
        work.resolve_work_phase(game_state)
        game_state.contract_factory.cleanup_end_of_phase()

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
            game_state.status = "ENDED"
            return

        game_state.contract_factory.cleanup_campfire_contracts()
        for player in game_state.players.values():
            player.consume_daily(
                {
                    "recovery": game_state.rules.RECOVERY_RATE,
                    "default": game_state.rules.DEFAULT_SICKNESS,
                    "hunger_increase": (
                        game_state.rules.HUNGER_SICKNESS_INCREASE
                    ),
                    "cold_increase": (
                        game_state.rules.COLD_SICKNESS_INCREASE
                    ),
                }
            )

        for development in list(game_state.developments.values()):
            still_exists = development.degrade()
            if not still_exists:
                game_state.developments.pop(development.id)
                owner = game_state.players.get(development.owner)
                if owner and development.id in owner.developments:
                    owner.developments.remove(development.id)

        game_state.actions = []
        if game_state.is_game_over():
            game_state.status = "ENDED"

    @staticmethod
    def start_day(game_state):
        work.start_work_phase(game_state)
        conflict.activate_pending_contests(game_state)
