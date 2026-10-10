from service.game.packet_handling.base import Command


ALLOWED_PLAYER_EMOJIS = {"👍", "❤️", "😂", "😠"}
REACTION_DURATION_SECONDS = 4


class SetEmojiCommand(Command):
    def execute(self, game_state, player):
        emoji = self.payload.get("emoji")
        if emoji not in ALLOWED_PLAYER_EMOJIS:
            return False
        player.reaction = {
            "emoji": emoji,
            "expires_at": game_state._clock() + REACTION_DURATION_SECONDS,
        }
        return True
