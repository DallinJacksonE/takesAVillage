from service.game.state.night import build_night_locations


class Player:
    def __init__(self, session_id, fire_status="COLD", fire_guests=None):
        self.session_id = session_id
        self.fire_status = fire_status
        self.fire_guests = list(fire_guests or [])


class Game:
    def __init__(self, players):
        self.players = {player.session_id: player for player in players}


def test_guest_seat_order_matches_fire_guest_acceptance_order():
    host = Player("host", "HOST", ["zebra", "alpha", "middle"])
    players = [host, Player("zebra"), Player("alpha"), Player("middle")]

    locations = build_night_locations(Game(players))

    assert locations["host"] == {"kind": "FIRE", "id": "host", "slot": 0}
    assert locations["zebra"] == {"kind": "FIRE", "id": "host", "slot": 1}
    assert locations["alpha"] == {"kind": "FIRE", "id": "host", "slot": 2}
    assert locations["middle"] == {"kind": "FIRE", "id": "host", "slot": 3}


def test_each_host_gets_a_separate_fire_anchor():
    host_a = Player("host-a", "HOST", ["guest-a"])
    host_b = Player("host-b", "HOST", ["guest-b"])
    players = [host_a, host_b, Player("guest-a"), Player("guest-b")]

    locations = build_night_locations(Game(players))

    assert locations["host-a"]["id"] == "host-a"
    assert locations["host-b"]["id"] == "host-b"
    assert locations["guest-a"]["id"] == "host-a"
    assert locations["guest-b"]["id"] == "host-b"
