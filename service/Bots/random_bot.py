import random
from base_bot import BaseBot


class RandomBot(BaseBot):

    def choose_action(self, game_state):

        possible_actions = self.get_possible_actions(game_state)

        if not possible_actions:
            return {
                "action_command": "FINISH_PHASE",
                "payload": {}
            }

        weighted = []

        for action in possible_actions:
            score = self.score_action(game_state, action)

            # Avoid negative weights
            score = max(1, score + 100)

            weighted.append((action, score))

        actions = [a for a, s in weighted]
        weights = [s for a, s in weighted]

        return random.choices(actions, weights=weights, k=1)[0]