# service/bots/base_bot.py

from abc import ABC


class BaseBot(ABC):

    def __init__(self, player_id):
        self.player_id = player_id

    def get_player(self, game_state):
        return game_state.players.get(self.player_id)

    def score_action(self, game_state, action):
        """
        Generic survival-first priorities.
        Subclasses can override this.
        """

        player = self.get_player(game_state)

        command = action["action_command"]

        score = 0

        # -------------------------
        # SURVIVAL
        # -------------------------

        # Low food is dangerous
        if player.resources["food"] <= 1:
            if command == "COMMIT_WORK":
                work_id = action["payload"].get("work_id")

                work = next(
                    (w for w in player.available_work if w.id == work_id),
                    None
                )

                if work and work.reward_type == "food":
                    score += 100

        # No warmth is dangerous
        if player.fire_status == "COLD":
            if command == "START_FIRE":
                score += 80

        # Sick players should prioritize recovery
        if player.health == "sick":
            if command == "START_FIRE":
                score += 50

        # -------------------------
        # ECONOMY
        # -------------------------

        if command == "BUILD_DEV":
            score += 40

        if command == "UPGRADE_DEV":
            score += 35

        if command == "MAINTAIN_DEV":
            score += 30

        # -------------------------
        # SOCIAL
        # -------------------------

        if command == "BARTER":
            score += 10

        # -------------------------
        # DEFAULT
        # -------------------------

        if command == "FINISH_PHASE":
            score -= 100

        return score

    def get_possible_actions(self, game_state):

        player = self.get_player(game_state)

        actions = []

        # -------------------------
        # WORK
        # -------------------------

        for work in player.available_work:
            actions.append({
                "action_command": "COMMIT_WORK",
                "payload": {
                    "work_id": work.id,
                }
            })

        # -------------------------
        # FIRE
        # -------------------------

        if player.fire_status == "COLD":
            if player.resources.get("wood", 0) > 0:
                actions.append({
                    "action_command": "START_FIRE",
                    "payload": {}
                })

        # -------------------------
        # BUILD DEV
        # -------------------------

        if (
            player.resources.get("wood", 0) >= 2 and
            player.resources.get("iron", 0) >= 1
        ):
            actions.append({
                "action_command": "BUILD_DEV",
                "payload": {
                    "dev_type": "FARM"
                }
            })

        # -------------------------
        # ALWAYS ALLOW END TURN
        # -------------------------

        actions.append({
            "action_command": "FINISH_PHASE",
            "payload": {}
        })

        return actions

    def choose_action(self, game_state):
        player = self.get_player(game_state)

        # Dead players do nothing
        if player.health == "dead":
            return {
                "action_command": "FINISH_PHASE",
                "payload": {}
            }

        # Already committed something this phase
        if game_state.phase == "WORK" and player.committed_action:
            return {
                "action_command": "FINISH_PHASE",
                "payload": {}
            }

        possible_actions = self.get_possible_actions(game_state)

        if not possible_actions:
            return {
                "action_command": "FINISH_PHASE",
                "payload": {}
            }

        scored = []

        for action in possible_actions:
            score = self.score_action(game_state, action)
            scored.append((score, action))

        scored.sort(key=lambda x: x[0], reverse=True)

        best_action = scored[0][1]

        return best_action
