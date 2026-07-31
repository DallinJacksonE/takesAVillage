from service.game.actions.base import Command


class StartFireCommand(Command):
    def execute(self, game_state, player):
        if game_state.phase != "NIGHT" or player.fire_status == "HOST":
            return False

        cost = game_state.campfire_cost.get("wood", 1)
        if self._deduct_resources(player, {"wood": cost}):
            player.fire_status = "HOST"
            player.fire_guests = []
            player.add_timeline_event(
                "ACTION_COMPLETED", {"action": "START_FIRE"}
            )
            return True
        return False


def seat_guest(game_state, contract):
    if getattr(contract, "is_request", False):
        host = game_state.players.get(contract.target_id)
        guest = game_state.players.get(contract.initiator_id)
    else:
        host = game_state.players.get(contract.initiator_id)
        guest = game_state.players.get(contract.target_id)

    if not host or not guest:
        return False
    if guest.fire_status == "GUEST":
        return False
    if getattr(host, "fire_status", "COLD") != "HOST":
        return False
    if len(getattr(host, "fire_guests", [])) >= game_state.max_fire_seats:
        return False

    host.fire_guests.append(guest.session_id)
    guest.fire_status = "GUEST"
    guests = list(host.fire_guests)
    guest.fire_history.append({
        "host_id": host.session_id,
        "fire_id": contract.id,
        "role": "guest",
        "guests": guests.copy(),
    })
    host.fire_history.append({
        "host_id": host.session_id,
        "fire_id": contract.id,
        "role": "host",
        "guests": guests.copy(),
    })
    host.add_timeline_event("SEATED_GUEST", {"guest": guest.session_id})
    guest.add_timeline_event("JOINED_FIRE", {"host": host.session_id})
    return True
