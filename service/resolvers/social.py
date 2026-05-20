
class SocialResolvers:
    @staticmethod
    def seat_guest(game_state, contract_obj):
        # Determine host and guest based on whether this is a request or offer
        # Offer (is_request=False): initiator is host, target is guest
        # Request (is_request=True): target is host, initiator is guest
        if getattr(contract_obj, 'is_request', False):
            host_player = game_state.players.get(contract_obj.target_id)
            guest_player = game_state.players.get(contract_obj.initiator_id)
        else:
            host_player = game_state.players.get(contract_obj.initiator_id)
            guest_player = game_state.players.get(contract_obj.target_id)

        if not host_player or not guest_player:
            return False
        if getattr(host_player, 'fire_status', 'COLD') != "HOST":
            return False
        if len(getattr(host_player, 'fire_guests',
                       [])) >= game_state.max_fire_seats:
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
        initiator = game_state.players.get(action.initiator_id)
        target = game_state.players.get(action.target_id)
        if not initiator or not target:
            return False

        # 1. Fill boxes (capped by actual inventory)
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

        # 2. Swap boxes
        for res, amt in initiator_box.items():
            target.resources[res] = target.resources.get(res, 0) + amt
        for res, amt in target_box.items():
            initiator.resources[res] = initiator.resources.get(res, 0) + amt

        initiator.add_timeline_event("TRADE_RESOLVED", {
                                     "trade_id": action.id,
                                     "sent": initiator_box,
                                     "received": target_box})
        target.add_timeline_event("TRADE_RESOLVED", {
                                  "trade_id": action.id,
                                  "sent": target_box,
                                  "received": initiator_box})
        trade_record_for_initiator = {
            "id": action.id,
            "initiator_id": action.initiator_id,
            "target_id": action.target_id,

            "offered": action.offer_items,
            "requested": action.request_items,

            "actual_sent": action.actual_offer_items,
            "actual_received": action.actual_request_items,
        }

        trade_record_for_target = {
            "id": action.id,
            "initiator_id": action.target_id,
            "target_id": action.initiator_id,

            "offered": action.request_items,
            "requested": action.offer_items,

            "actual_sent": action.actual_request_items,
            "actual_received": action.actual_offer_items
        }
        initiator.trade_history.append(trade_record_for_initiator)
        target.trade_history.append(trade_record_for_target)
        return True
