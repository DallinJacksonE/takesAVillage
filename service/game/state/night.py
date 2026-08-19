"""Pure NIGHT-scene placement helpers."""


def build_night_locations(game):
    """Return deterministic public clearing locations for every player."""
    locations = {}
    players = sorted(game.players.values(), key=lambda player: player.session_id)
    cold_players = []

    for player in players:
        if player.fire_status == "HOST":
            locations[player.session_id] = {
                "kind": "FIRE",
                "id": player.session_id,
                "slot": 0,
            }
            for slot, guest_id in enumerate(sorted(player.fire_guests), start=1):
                if guest_id in game.players:
                    locations[guest_id] = {
                        "kind": "FIRE",
                        "id": player.session_id,
                        "slot": slot,
                    }

    for player in players:
        if player.session_id not in locations:
            cold_players.append(player.session_id)

    for slot, player_id in enumerate(cold_players):
        locations[player_id] = {"kind": "NIGHT_COLD", "slot": slot}

    return locations
