class Player:
    def __init__(self, session_id, name):
        self.session_id = session_id
        self.name = name
        self.resources = {"food": 5, "wood": 2, "iron": 0}
        self.health = "healthy"  # healthy, sick, recovering
        self.sickness_chance = 0.05
        self.developments = []  # List of IDs owned by this player
        self.messages = {}  # msgId : msg

        # Phase specific states
        self.hosting_fire = False
        self.current_fire_host = None  # ID of player sharing fire with messages
        self.available_work = self.developments
        self.finished_phase = False

    def consume_daily(self):
        """Logic for nightly consumption and sickness calculation."""
        # 1. Food
        ate = False
        if self.resources['food'] > 0:
            self.resources['food'] -= 1
            ate = True

        # 2. Wood (Warmth)
        warm = False
        if self.current_fire_host:
            warm = True  # Shared fire
        elif self.resources['wood'] > 0:
            self.resources['wood'] -= 1
            warm = True

        # 3. Health Calc
        if not ate:
            self.sickness_chance += 0.2
        if not warm:
            self.sickness_chance += 0.1

        # Chance to get sick
        import random
        if random.random() < self.sickness_chance:
            self.health = "sick"
        elif self.health == "sick" and ate and warm:
            self.health = "recovering"
        elif self.health == "recovering" and ate and warm:
            self.health = "healthy"
            self.sickness_chance = 0.05  # Reset base chance

        # Reset daily flags
        self.current_fire_host = None
        self.hosting_fire = False
        self.action_locked = False
        self.available_work = self.developments

    def reset_phase(self):
        self.available_work = self.developments
        self.finished_phase = False

    def to_dict(self):
        return {
            "name": self.name,
            "resources": self.resources,
            "health": self.health,
            "sickness_chance": self.sickness_chance,
            "developments": self.developments,
            "finished_phase": self.finished_phase,
            "messages": [m.to_dict() for m in self.messages.values()],
            "available_work": self.available_work
        }
