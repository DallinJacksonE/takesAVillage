import random

from base_bot import BaseBot

class EconBot(BaseBot):

    def score_action(self, game_state, action):

        score = super().score_action(game_state, action)

        command = action["action_command"]

        # Loves economy
        if command == "BUILD_DEV":
            score += 30

        if command == "UPGRADE_DEV":
            score += 50

        # Doesn't care much about social
        if command == "BARTER":
            score -= 5

        return score