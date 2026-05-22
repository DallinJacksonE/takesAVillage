# service/bots/bot_manager.py

from actions.action_dispatcher import ActionDispatcher


class BotManager:

    def __init__(self):
        self.bots = {}

    def register_bot(self, bot):
        self.bots[bot.player_id] = bot

    def run_turn(self, game_state):

        for player_id, bot in self.bots.items():

            player = game_state.players.get(player_id)

            if not player:
                continue

            if player.finished_phase:
                continue

            action_data = bot.choose_action(game_state)

            if not action_data:
                continue

            try:
                ActionDispatcher.dispatch(
                    game_state,
                    player_id,
                    action_data
                )

            except Exception as e:
                print(f"BOT ERROR {player_id}: {e}")