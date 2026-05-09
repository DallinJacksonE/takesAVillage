from constants import CAMPFIRE_COST, MAX_FIRE_SEATS


class SocialSystem:
    @staticmethod
    def start_fire(game_state, player):
        """Allows a player to spend wood to become a HOST."""
        # NEW: Restricted strictly to the NIGHT phase
        if game_state.phase != 'NIGHT':
            return False

        if player.fire_status == "HOST":
            return False  # Already hosting a fire

        cost = CAMPFIRE_COST.get("wood", 1)
        if player.resources.get("wood", 0) >= cost:
            player.resources["wood"] -= cost
            player.fire_status = "HOST"
            player.fire_guests = []

            player.add_timeline_event(
                "ACTION_COMPLETED", {"action": "START_FIRE"})
            return True

        return False

    @staticmethod
    def seat_guest(game_state, host_player, action_obj):
        """Processes an accepted CAMPFIRE contract."""
        guest_player = game_state.players.get(action_obj.initiator_id)
        if not guest_player:
            return False

        if getattr(host_player, 'fire_status', 'COLD') != "HOST":
            return False

        if len(getattr(host_player, 'fire_guests', [])) >= MAX_FIRE_SEATS:
            return False

        host_player.fire_guests.append(guest_player.session_id)
        guest_player.fire_status = "GUEST"

        host_player.add_timeline_event(
            "SEATED_GUEST", {"guest": guest_player.session_id})
        guest_player.add_timeline_event(
            "JOINED_FIRE", {"host": host_player.session_id})

        return True

    @staticmethod
    def execute_trade(game_state, action):
        """Executes the Prisoner's Dilemma box swap instantly upon completion."""
        initiator = game_state.players.get(action.initiator_id)
        target = game_state.players.get(action.target_id)

        if not initiator or not target:
            return False

        # 1. Fill the boxes (capped by actual inventory to prevent negative balances)
        initiator_box = {}
        for res, amt in getattr(action, 'actual_offer_items', {}).items():
            actual_amt = min(amt, initiator.resources.get(res, 0))
            initiator_box[res] = actual_amt
            initiator.resources[res] -= actual_amt

        target_box = {}
        for res, amt in getattr(action, 'actual_request_items', {}).items():
            actual_amt = min(amt, target.resources.get(res, 0))
            target_box[res] = actual_amt
            target.resources[res] -= actual_amt

        # 2. Swap the boxes
        for res, amt in initiator_box.items():
            target.resources[res] = target.resources.get(res, 0) + amt

        for res, amt in target_box.items():
            initiator.resources[res] = initiator.resources.get(res, 0) + amt

        # Log the reality of the trade
        initiator.add_timeline_event("TRADE_RESOLVED", {
                                     "trade_id": action.id, "sent": initiator_box, "received": target_box})
        target.add_timeline_event("TRADE_RESOLVED", {
                                  "trade_id": action.id, "sent": target_box, "received": initiator_box})

        return True
