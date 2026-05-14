import time
import uuid
import random


class Player:
    def __init__(self, session_id, name, starting_resources, sickness_chance):
        self.session_id = session_id
        self.name = name
        self.resources = starting_resources
        self.health = "healthy"  # healthy, sick, recovering, dead
        # CHANGE THIS TO MATCH THE GAMESTATE STARTING SICKNESS CHANCE
        self.sickness_chance = sickness_chance
        self.developments = []  # List of IDs owned by this player

        self.actions = {}
        self.timeline = []  # Chronological log for research data extraction

        # Phase specific states
        self.fire_status = "COLD"  # COLD, HOST, GUEST
        self.fire_guests = []
        self.available_work = self.developments
        self.finished_phase = False
        self.committed_action = None

    def add_timeline_event(self, event_type, data):
        """
        Appends an event to the player's history for research tracking.
        event_type examples: 'CHAT', 'ACTION_DRAFTED', 'ACTION_COMMITTED'
        """
        self.timeline.append({
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "type": event_type,
            "data": data
        })

    def update_sickness_chance(self, ate: bool, warm: bool, sickness_rules):

        if self.sickness_chance is None:
            self.sickness_chance = sickness_rules["default"]
        if not ate:
            self.sickness_chance += sickness_rules["hunger_increase"]
        if not warm:
            self.sickness_chance += sickness_rules["cold_increase"]

        # Recovery only happens with both eating and warm
        if warm and ate:
            self.sickness_chance = max(
                sickness_rules["default"],
                self.sickness_chance - sickness_rules["recovery"])

    def update_health(self, ate: bool, warm: bool,
                      check: float, sickness_rules):
        for key, value in sickness_rules.items():
            print(f"Key: {key} \nValue: {value}")
        self.update_sickness_chance(ate, warm, sickness_rules)
        if self.health == "dead":
            return "dead"
        elif (check < self.sickness_chance
              and self.health == "sick" and (not ate or not warm)):
            return "dead"
        elif check < self.sickness_chance:
            return "sick"
        elif self.health == "sick" and ate and warm:
            return "recovering"
        elif self.health == "recovering" and ate and warm:
            self.sickness_chance = sickness_rules["default"]
            return "healthy"
        else:
            return "healthy"

    def consume_daily(self, sickness_rules):
        """Logic for nightly consumption and sickness calculation."""

        if not self.sickness_chance:
            self.sickness_chance = sickness_rules["default"]

        # Food
        ate = False
        if self.resources['food'] > 0:
            self.resources['food'] -= 1
            ate = True

        # Wood
        warm = False
        if self.fire_status in ["HOST", "GUEST"]:
            warm = True

        check = random.random()

        self.health = self.update_health(ate, warm, check, sickness_rules)

        self.add_timeline_event("END_OF_DAY_STATE", {
            "health": self.health,
            "resources": self.resources.copy(),
            "sickness_chance": self.sickness_chance
        })

        # Daily flags
        self.fire_status = "COLD"
        self.fire_guests = []  # Reset to nobody for the next day
        self.available_work = self.developments

    def reset_phase(self):
        self.available_work = self.developments
        self.finished_phase = False
        self.fire_guests = []

    def to_dict(self):
        return {
            "name": self.name,
            "resources": self.resources,
            "health": self.health,
            "sickness_chance": self.sickness_chance,
            "developments": self.developments,
            "fire_status": self.fire_status,
            "finished_phase": self.finished_phase,
            "actions": [a.__dict__ for a in self.actions.values()],
            "timeline": self.timeline,
            "available_work": self.available_work
        }
