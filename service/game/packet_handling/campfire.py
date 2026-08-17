from service.game.packet_handling.base import Command
from service.game.state.events import (
    FireStarted,
    GuestSeatedAtFire,
    PlayerResourcesSpent,
)


class StartFireCommand(Command):
    def execute(self, game_state, player):
        if game_state.phase != "NIGHT" or player.fire_status == "HOST":
            return False

        cost = game_state.campfire_cost.get("wood", 1)
        if player.resources.get("wood", 0) < cost:
            return False
        game_state.apply_events([
            PlayerResourcesSpent(player.session_id, {"wood": cost}),
            FireStarted(player.session_id),
        ])
        player.add_timeline_event(
            "ACTION_COMPLETED", {"action": "START_FIRE"}
        )
        return True


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

    game_state.apply_event(GuestSeatedAtFire(
        contract.id,
        host.session_id,
        guest.session_id,
    ))
    return True
