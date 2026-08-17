from service.game.packet_handling.campfire import StartFireCommand
from service.game.packet_handling.contracts import CampfireContract


def update_contract(game, actor_id, contract, action_command, payload=None):
    data = {"action_id": contract.id, **(payload or {})}
    return game.contract_factory.process_contract(actor_id, data, action_command)


def test_fire_host_cannot_send_duplicate_invitations_to_same_guest(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    host = game.players["player-1"]
    guest = game.players["player-2"]
    host.fire_status = "HOST"

    first_status, first_contract = game.contract_factory.process_contract(
        host.session_id,
        {"type": "CAMPFIRE", "target_id": guest.session_id},
    )
    duplicate_status, duplicate_contract = game.contract_factory.process_contract(
        host.session_id,
        {"type": "CAMPFIRE", "target_id": guest.session_id},
    )

    assert first_status == "CREATED"
    assert first_contract is not None
    assert duplicate_status == "ILLEGAL"
    assert duplicate_contract is first_contract
    campfire_actions = [
        action for action in host.actions.values()
        if getattr(action, "type", None) == "CAMPFIRE"
    ]
    assert len(campfire_actions) == 1


def test_fire_host_cannot_accept_duplicate_requests_from_same_guest(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    host = game.players["player-1"]
    guest = game.players["player-2"]
    host.fire_status = "HOST"
    first_request = CampfireContract(guest.session_id, host.session_id, is_request=True)
    duplicate_request = CampfireContract(guest.session_id, host.session_id, is_request=True)
    game.contract_factory._add_contract_to_players(first_request)
    game.contract_factory._add_contract_to_players(duplicate_request)

    first_status, accepted = update_contract(
        game, host.session_id, first_request, "ACCEPT")
    second_status, unchanged = update_contract(
        game, host.session_id, duplicate_request, "ACCEPT")

    assert first_status == "UPDATED_ACCEPTED"
    assert accepted.status == "ACCEPTED"
    assert second_status == "ILLEGAL"
    assert unchanged.status == "PENDING"
    assert host.fire_guests == [guest.session_id]
    assert guest.fire_status == "GUEST"


def test_fire_guests_are_warm_during_night_consumption(make_game, monkeypatch):
    game = make_game(player_ids=("player-1", "player-2"))
    host = game.players["player-1"]
    guest = game.players["player-2"]
    game.phase = "NIGHT"
    host.resources["wood"] = 2
    guest.resources["food"] = 1
    guest.sickness_chance = game.rules.DEFAULT_SICKNESS
    assert StartFireCommand(host.session_id, {}).execute(game, host) is True
    contract = CampfireContract(host.session_id, guest.session_id)
    game.contract_factory._add_contract_to_players(contract)
    update_contract(game, guest.session_id, contract, "ACCEPT")
    monkeypatch.setattr(
        "service.game.models.player.random.random", lambda: 1.0)

    guest.consume_daily({
        "recovery": game.rules.RECOVERY_RATE,
        "default": game.rules.DEFAULT_SICKNESS,
        "hunger_increase": game.rules.HUNGER_SICKNESS_INCREASE,
        "cold_increase": game.rules.COLD_SICKNESS_INCREASE,
    })

    assert guest.timeline[-1]["data"]["sickness_chance"] == game.rules.DEFAULT_SICKNESS
    assert guest.health == "healthy"
