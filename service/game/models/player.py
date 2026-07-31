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
        self.trade_history = []  # Log of trades for research and player reference
        self.old_history = []
        self.fire_history = []

        # Phase specific states
        self.fire_status = "COLD"  # COLD, HOST, GUEST
        self.fire_guests = []
        self.available_work = []
        self.finished_phase = False
        self.committed_action = None
        self.last_committed_action = None
        self.trade_count = 0

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

        self.update_sickness_chance(ate, warm, sickness_rules)

        if self.health == "dead":
            return "dead"

        # Recovery path first
        if ate and warm:
            if self.health == "sick":
                return "recovering"

            elif self.health == "recovering":
                self.sickness_chance = sickness_rules["default"]
                return "healthy"

        # Normal sickness checks
        if check < self.sickness_chance:
            if self.health == "sick":
                return "dead"
            else:
                return "sick"

        # No sickness roll triggered
        return self.health

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
        self.available_work = []

    def reset_phase(self):
        if self.health != "dead":
            self.finished_phase = False
        else:
            self.finished_phase = True
        self.fire_guests = []

    def to_dict(self) -> dict:
        """
        Serializes the Player into a dictionary, ensuring all nested
        (like Development) call their specific to_dict() methods to maintain
        naming consistency and prevent JSON errors.
        """
        return {
            "id": self.session_id,
            "name": self.name,
            "health": self.health,
            "sickness_chance": self.sickness_chance,
            "fire_status": self.fire_status,
            "fire_guests": self.fire_guests,
            "resources": self.resources,

            "developments": [
                d for d in self.developments
            ],

            # Convert values array to list of dicts safely
            "actions": [
                a.to_dict() if hasattr(a, 'to_dict') else a.__dict__
                for a in self.actions.values()
            ],
            "timeline": self.timeline,
            "finished_phase": self.finished_phase,

            "available_work": [
                w.to_dict() if hasattr(w, 'to_dict') else w
                for w in self.available_work
            ],

            "committed_action": (
                self.committed_action.to_dict() if hasattr(
                    self.committed_action, 'to_dict')
                else self.committed_action
            ) if self.committed_action else None,

            "trade_history": self.trade_history, # Assuming trade_history is already a list of dicts or simple data
            "fire_history": self.fire_history[-5:]  # Last 5 fire interactions
        }


"""export interface PlayerDTO {
  id: string;
  name: string;
  health: "healthy" | "sick" | "recovering" | "dead";
  sickness_chance: number;
  fire_status: "COLD" | "HOST" | "GUEST";
  fire_guests?: string[];
  resources: ResourceBundle;
  developments: string[];
  available_work: WorkActionDTO[];
  committed_action: WorkActionDTO | ContestActionDTO | null;
  actions: ActionDTO[];
  timeline: any[]; // Lightweight research log left as any[]
  finished_phase: boolean;
"""