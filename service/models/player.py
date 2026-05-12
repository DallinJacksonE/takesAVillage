import time
import uuid
import random


class Player:
    def __init__(self, session_id, name, starting_resources):
        self.session_id = session_id
        self.name = name
        self.resources = starting_resources
        self.health = "healthy"  # healthy, sick, recovering, dead
        self.sickness_chance = None
        self.developments = []  # List of IDs owned by this player

        # --- The New Unified Action & Research Data ---
        self.actions = {}  # action_id : Action Object
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
        event_type examples: 'CHAT', 'ACTION_DRAFTED', 'ACTION_COMMITTED', 'PHASE_CHANGE'
        """
        self.timeline.append({
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "type": event_type,
            "data": data
        })

    def consume_daily(self, gamestate):
        """Logic for nightly consumption and sickness calculation."""
        # 1. Food
        ate = False
        if self.resources['food'] > 0:
            self.resources['food'] -= 1
            ate = True

        # 2. Wood (Warmth via the new fire_status logic)
        warm = False
        if self.fire_status in ["HOST", "GUEST"]:
            warm = True
        elif self.resources['wood'] > 0:
            self.resources['wood'] -= 1
            warm = True

        # 3. Health Calc
        if self.sickness_chance is None:
            self.sickness_chance = gamestate.starting_sickness_chance
        if not ate:
            self.sickness_chance += gamestate.hunger_sickness_increase
        if not warm:
            self.sickness_chance += gamestate.cold_sickness_increase

        # Chance to get sick
        check = random.random()
        if check < self.sickness_chance and self.health == "sick" and (not ate or not warm):
            self.health = "dead"
        if check < self.sickness_chance:
            self.health = "sick"
        elif self.health == "sick" and ate and warm:
            self.health = "recovering"
        elif self.health == "recovering" and ate and warm:
            self.health = "healthy"
            self.sickness_chance = gamestate.starting_sickness_chance  # Reset base chance

        # Log the end of day state for the research timeline
        self.add_timeline_event("END_OF_DAY_STATE", {
            "health": self.health,
            "resources": self.resources.copy(),
            "sickness_chance": self.sickness_chance
        })

        # Reset daily flags
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
