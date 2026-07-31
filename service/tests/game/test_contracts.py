from math import nan

from service.game.actions.contracts import (
    CampfireContract,
    EmploymentContract,
    execute_trade,
)
from service.game.models.development import Development


def create_contract(game, actor_id, payload):
    status, contract = game.contract_factory.process_contract(
        actor_id, payload, payload.get("action_command")
    )
    return status, contract


def update_contract(game, actor_id, contract, action_command, payload=None):
    data = {"action_id": contract.id, **(payload or {})}
    return game.contract_factory.process_contract(actor_id, data, action_command)


def test_trade_finalization_swaps_inventory_and_records_history(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    first.resources = {"food": 3, "wood": 0, "iron": 0}
    second.resources = {"food": 0, "wood": 2, "iron": 0}

    created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 2},
        "request_items": {"wood": 1},
    })
    accepted, _ = update_contract(game, second.session_id, trade, "ACCEPT")
    update_contract(
        game, first.session_id, trade, "FINALIZE", {"actual_items": {"food": 2}}
    )
    completed, finalized_trade = update_contract(
        game, second.session_id, trade, "FINALIZE", {"actual_items": {"wood": 1}}
    )
    executed = execute_trade(game, finalized_trade)

    assert created == "CREATED"
    assert accepted == "UPDATED_ACCEPTED"
    assert completed == "UPDATED_COMPLETED"
    assert executed is True
    assert first.resources == {"food": 1, "wood": 1, "iron": 0}
    assert second.resources == {"food": 2, "wood": 1, "iron": 0}
    assert first.trade_history[0]["actual_sent"] == {"food": 2}
    assert second.trade_history[0]["actual_received"] == {"food": 2}


def test_trade_execution_caps_actual_items_to_available_inventory(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    first.resources = {"food": 1, "wood": 0, "iron": 0}
    second.resources = {"food": 0, "wood": 0, "iron": 0}

    _created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 5},
        "request_items": {},
    })
    trade.actual_offer_items = {"food": 5}
    trade.actual_request_items = {}

    execute_trade(game, trade)

    assert first.resources["food"] == 0
    assert second.resources["food"] == 1
    assert first.trade_history[0]["actual_sent"] == {"food": 1}
    assert second.trade_history[0]["actual_received"] == {"food": 1}


def test_trade_rejects_negative_actual_amounts_without_mutating_inventory(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    first.resources = {"food": 3, "wood": 0, "iron": 0}
    second.resources = {"food": 0, "wood": 2, "iron": 0}
    _created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {},
    })
    trade.status = "COMPLETED"
    trade.actual_offer_items = {"food": -2}
    trade.actual_request_items = {}

    assert execute_trade(game, trade) is False
    assert first.resources == {"food": 3, "wood": 0, "iron": 0}
    assert second.resources == {"food": 0, "wood": 2, "iron": 0}
    assert first.trade_history == []
    assert second.trade_history == []


def test_trade_rejects_non_finite_actual_amounts(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    first.resources = {"food": 3, "wood": 0, "iron": 0}
    second.resources = {"food": 0, "wood": 2, "iron": 0}
    _created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {},
    })
    trade.actual_offer_items = {"food": nan}
    trade.actual_request_items = {}

    assert execute_trade(game, trade) is False
    assert first.resources["food"] == 3
    assert second.resources["food"] == 0


def test_deceptive_trade_finalization_increments_lie_count(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    _created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 2},
        "request_items": {},
    })

    _accepted, trade = update_contract(
        game, second.session_id, trade, "ACCEPT")
    update_contract(game, first.session_id, trade, "FINALIZE", {"actual_items": {}})
    update_contract(game, second.session_id, trade, "FINALIZE", {"actual_items": {}})

    assert game.lie_count == {first.session_id: 1}


def test_employment_acceptance_assigns_worker_and_available_job(make_game):
    game = make_game()
    employer = game.players["player-1"]
    worker = game.players["player-2"]
    development = Development(
        "dev-1", "Farm", employer.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    game.developments[development.id] = development
    employer.developments.append(development.id)
    contract = EmploymentContract(
        employer.session_id, worker.session_id,
        development.id, 2, "food", is_application=False,
    )
    game.contract_factory._add_contract_to_players(contract)

    status, accepted = update_contract(
        game, worker.session_id, contract, "ACCEPT"
    )

    assert status == "UPDATED_ACCEPTED"
    assert accepted.status == "ACCEPTED"
    assert development.worker_id == worker.session_id
    assert worker.available_work[0]["development"]["id"] == development.id
    assert worker.available_work[0]["wage"] == 2


def test_employment_creation_rejects_development_owned_by_another_player(make_game):
    game = make_game()
    owner = game.players["player-1"]
    would_be_employer = game.players["player-2"]
    development = Development(
        "dev-1", "Farm", owner.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    game.developments[development.id] = development
    owner.developments.append(development.id)

    status, contract = create_contract(game, would_be_employer.session_id, {
        "type": "EMPLOYMENT",
        "target_id": owner.session_id,
        "dev_id": development.id,
        "wage": 1,
        "wage_type": "food",
    })

    assert status == "ERROR"
    assert contract is None


def test_employment_acceptance_rechecks_current_development_owner(make_game):
    game = make_game()
    employer = game.players["player-1"]
    worker = game.players["player-2"]
    development = Development(
        "dev-1", "Farm", employer.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    game.developments[development.id] = development
    employer.developments.append(development.id)
    _created, contract = create_contract(game, employer.session_id, {
        "type": "EMPLOYMENT",
        "target_id": worker.session_id,
        "dev_id": development.id,
        "wage": 1,
        "wage_type": "food",
    })
    development.owner = worker.session_id

    status, unchanged = update_contract(
        game, worker.session_id, contract, "ACCEPT")

    assert status == "ILLEGAL"
    assert unchanged.status == "PENDING"
    assert getattr(development, "worker_id", None) is None
    assert worker.available_work == []


def test_campfire_acceptance_seats_guest_once(make_game):
    game = make_game()
    host = game.players["player-1"]
    guest = game.players["player-2"]
    host.fire_status = "HOST"
    contract = CampfireContract(host.session_id, guest.session_id)
    game.contract_factory._add_contract_to_players(contract)

    status, accepted = update_contract(game, guest.session_id, contract, "ACCEPT")
    duplicate_status, _ = update_contract(game, guest.session_id, accepted, "ACCEPT")

    assert status == "UPDATED_ACCEPTED"
    assert duplicate_status == "ILLEGAL"
    assert host.fire_guests == [guest.session_id]
    assert guest.fire_status == "GUEST"


def test_campfire_acceptance_rejects_full_fire_without_mutation(make_game):
    game = make_game()
    host = game.players["player-1"]
    guest = game.players["player-2"]
    host.fire_status = "HOST"
    host.fire_guests = [f"guest-{index}" for index in range(game.max_fire_seats)]
    contract = CampfireContract(host.session_id, guest.session_id)
    game.contract_factory._add_contract_to_players(contract)

    status, unchanged = update_contract(game, guest.session_id, contract, "ACCEPT")

    assert status == "ILLEGAL"
    assert unchanged.status == "PENDING"
    assert guest.fire_status == "COLD"
    assert len(host.fire_guests) == game.max_fire_seats


def test_barter_and_cancel_update_existing_trade_contract(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    _created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {"wood": 1},
    })

    bartered, trade = update_contract(
        game, second.session_id, trade, "BARTER",
        {"offer_items": {"food": 2}, "request_items": {}},
    )
    cancelled, trade = update_contract(
        game, first.session_id, trade, "CANCEL",
    )

    assert bartered == "UPDATED_PENDING"
    assert trade.offer_items == {"food": 2}
    assert cancelled == "UPDATED_CANCELED"
    assert trade.status == "CANCELED"


def test_contract_rejects_non_party_and_wrong_turn_updates(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    game.add_player("player-3")
    outsider = game.players["player-3"]
    _created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {},
    })

    outsider_status, _ = update_contract(
        game, outsider.session_id, trade, "ACCEPT")
    wrong_turn_status, _ = update_contract(
        game, first.session_id, trade, "ACCEPT")

    assert outsider_status == "ILLEGAL"
    assert wrong_turn_status == "ILLEGAL"
    assert trade.status == "PENDING"
