class Perception:
    """
    The Sense module. Strictly a 'camera'. Parses the raw game_state JSON 
    and translates it into a clean, objective 'Memory' state.
    """

    def __init__(self):
        pass

    def sense(self, game_state: dict) -> dict:
        """
        Reads the world and returns a normalized memory state without judgments.
        """
        me = game_state.get("me", {})
        my_id = me.get("id")
        resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})

        # --- 1. Action / Blocking States ---
        is_waiting = any(
            action.get("type") == "EMPLOYMENT"
            and action.get("is_application")
            and action.get("initiator_id") == my_id
            and action.get("status") == "PENDING"
            for action in me.get("actions", [])
        )

        pending_contracts = [
            a for a in me.get("actions", [])
            if a.get("status") in ["PENDING", "ACCEPTED"]
        ]

        # --- 2. Development State Categorization ---
        # Splitting developments into distinct categories makes it much easier
        # for the GOAP planner to target the right lists later.
        developments = game_state.get("developments", [])

        my_developments = []
        unowned_developments = []
        other_player_developments = []  # This is crucial for your contesting logic

        for dev in developments:
            owner_id = dev.get("owner_id")
            if owner_id == my_id:
                my_developments.append(dev)
            elif not owner_id:
                unowned_developments.append(dev)
            else:
                other_player_developments.append(dev)

        # --- 3. Construct the Factual Memory Object ---
        memory = {
            # Core State
            "phase": game_state.get("phase"),
            "health": me.get("health"),
            "sickness_chance": me.get("sickness_chance", 0.0),
            "is_waiting": is_waiting,

            # Pure resource counts
            "food": resources.get("food", 0),
            "wood": resources.get("wood", 0),
            "iron": resources.get("iron", 0),

            # World metrics
            "pending_contracts": pending_contracts,
            "available_work": me.get("available_work", []),

            # Development Data (Passing the full objects)
            "my_developments": my_developments,
            "unowned_developments": unowned_developments,
            "other_player_developments": other_player_developments
        }

        return memory
