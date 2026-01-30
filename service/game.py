import uuid
import random


class Player:
    def __init__(self, session_id):
        self.session_id = session_id
        # Resources
        self.resources = {
            "fire": 0,
            "food": 5,  # Starting food
            "ferrous": 0
        }
        # Health: 'healthy', 'sick', 'recovering'
        self.health = "healthy"
        self.sickness_chance = 0.05

        # Sentiments: Dictionary mapping other_player_id -> score (-2 to 2)
        self.sentiments = {}

        # Developments: list of dicts
        # e.g. {'type': 'Farm', 'level': 1, 'maintenance_days': 5}
        self.developments = []

    def to_dict(self):
        return {
            "resources": self.resources,
            "health": self.health,
            "sickness_chance": self.sickness_chance,
            "developments": self.developments,
            "sentiments": self.sentiments
        }


class Game:
    def __init__(self, game_id, host_id):
        self.game_id = game_id
        self.host_id = host_id
        self.players = {}  # Map session_id -> Player obj
        self.state = "WAITING"  # WAITING, RUNNING, FINISHED
        self.day = 1
        self.phase = "WORK"  # WORK, TRADE, RUMOR, NIGHT

    def add_player(self, session_id):
        if self.state == "WAITING":
            self.players[session_id] = Player(session_id)
            # Initialize neutral sentiment (0) for all existing players toward new player
            # and vice versa
            return True
        return False

    def start_game(self):
        if len(self.players) > 1:  # Need at least 2 to play
            self.state = "RUNNING"
            self.day = 1
            self.phase = "WORK"
            return True
        return False

    def next_phase(self):
        phases = ["WORK", "TRADE", "RUMOR", "NIGHT"]
        current_idx = phases.index(self.phase)

        if self.phase == "NIGHT":
            self.day += 1
            self.phase = "WORK"
            # Logic for food consumption/sickness calc goes here
        else:
            self.phase = phases[current_idx + 1]

    def get_state_for_player(self, session_id):
        """
        Returns the sanitized game state for a specific player.
        (Players shouldn't see everyone else's hidden resources, potentially).
        """
        me = self.players.get(session_id)
        if not me:
            return None

        return {
            "game_id": self.game_id,
            "status": self.state,
            "day": self.day,
            "phase": self.phase,
            "me": me.to_dict(),
            "player_count": len(self.players),
            "is_host": session_id == self.host_id
        }
