import time
import uuid
import random

from service.game.state.health import next_sickness_chance, transition_health
from service.game.state.player_phase import (
    LOCKED_PHASE_STATES,
    PlayerPhaseState,
)


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
        self.phase_state = PlayerPhaseState.ACTIVE.value
        self.committed_action = None
        self.last_committed_action = None
        self.trade_count = 0
        self.reaction = None

    @property
    def finished_phase(self):
        return self.phase_state in LOCKED_PHASE_STATES

    @finished_phase.setter
    def finished_phase(self, is_finished):
        if self.phase_state == PlayerPhaseState.DEAD.value:
            return
        self.phase_state = (
            PlayerPhaseState.RESOLVED.value
            if is_finished
            else PlayerPhaseState.ACTIVE.value
        )

    def submit_phase_intent(self):
        if self.phase_state != PlayerPhaseState.DEAD.value:
            self.phase_state = PlayerPhaseState.INTENT_SUBMITTED.value

    def require_phase_replacement(self):
        if self.phase_state != PlayerPhaseState.DEAD.value:
            self.phase_state = PlayerPhaseState.NEEDS_REPLACEMENT.value

    def resolve_phase(self):
        if self.phase_state != PlayerPhaseState.DEAD.value:
            self.phase_state = PlayerPhaseState.RESOLVED.value

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

        self.sickness_chance = next_sickness_chance(
            self.sickness_chance, ate, warm, sickness_rules)

    def update_health(self, ate: bool, warm: bool,
                  check: float, sickness_rules):

        result = transition_health(
            self.health, self.sickness_chance, ate, warm, check,
            sickness_rules)
        self.sickness_chance = result.sickness_chance
        return result.health

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
            self.phase_state = PlayerPhaseState.ACTIVE.value
        else:
            self.phase_state = PlayerPhaseState.DEAD.value
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
            "phase_state": self.phase_state,

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