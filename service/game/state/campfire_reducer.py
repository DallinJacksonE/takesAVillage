"""Campfire event appliers for the game-state reducer."""


class CampfireReducer:
    def _remove_guest_from_existing_fires(self, game, guest_id):
        for player in game.players.values():
            if guest_id in getattr(player, "fire_guests", []):
                player.fire_guests = [
                    current_id for current_id in player.fire_guests
                    if current_id != guest_id
                ]

    def _apply_fire_started(self, game, event):
        player = game.players[event.player_id]
        self._remove_guest_from_existing_fires(game, player.session_id)
        player.fire_status = "HOST"
        player.fire_guests = []
        return player

    def _apply_guest_seated_at_fire(self, game, event):
        host = game.players[event.host_id]
        guest = game.players[event.guest_id]
        self._remove_guest_from_existing_fires(game, guest.session_id)
        if guest.session_id not in host.fire_guests:
            host.fire_guests.append(guest.session_id)
        guest.fire_status = "GUEST"
        guests = list(host.fire_guests)
        guest.fire_history.append({
            "host_id": host.session_id,
            "fire_id": event.contract_id,
            "role": "guest",
            "guests": guests.copy(),
        })
        host.fire_history.append({
            "host_id": host.session_id,
            "fire_id": event.contract_id,
            "role": "host",
            "guests": guests.copy(),
        })
        host.add_timeline_event("SEATED_GUEST", {"guest": guest.session_id})
        guest.add_timeline_event("JOINED_FIRE", {"host": host.session_id})
        return guest
