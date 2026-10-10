import json
from math import nan

import pytest

from service.game.packet_handling.contracts import (
    CampfireContract,
    EmploymentContract,
    TradeContract,
    execute_trade,
)
from service.game.models.development import Development
from service.game.state.events import (
    ContractCreated,
    ContractExpired,
    ContractRemoved,
    ContractUpdated,
    EmploymentAccepted,
    PlayerResourcesTransferred,
    TradeFinalized,
)


def create_contract(game, actor_id, payload):
    status, contract = game.contract_factory.process_contract(
        actor_id, payload, payload.get("action_command")
    )
    return status, contract


def update_contract(game, actor_id, contract, action_command, payload=None):
    data = {"action_id": contract.id, **(payload or {})}
    return game.contract_factory.process_contract(actor_id, data, action_command)


def owned_development(game, owner, dev_id="dev-1"):
    development = Development(
        dev_id, "Farm", owner.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    game.developments[development.id] = development
    owner.developments.append(development.id)
    return development


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
    assert completed == "UPDATED_FINALIZED"
    assert executed is True
    assert first.resources == {"food": 1, "wood": 1, "iron": 0}
    assert second.resources == {"food": 2, "wood": 1, "iron": 0}
    assert game.domain_events[-2:] == [
        PlayerResourcesTransferred(
            first.session_id, second.session_id, {"food": 2}),
        PlayerResourcesTransferred(
            second.session_id, first.session_id, {"wood": 1}),
    ]
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
    assert game.domain_events[-1] == PlayerResourcesTransferred(
        first.session_id, second.session_id, {"food": 1})
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
    trade.status = "FINALIZED"
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
    assert game.domain_events[-2] == TradeFinalized(
        trade.id,
        initiator_lied=True,
        target_lied=False,
    )


def test_employment_acceptance_projects_available_job_without_worker_binding(make_game):
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
    assert getattr(development, "worker_id", None) is None
    assert worker.available_work[0]["development"]["id"] == development.id
    assert worker.available_work[0]["wage"] == 2
    assert game.domain_events[-2:] == [
        ContractUpdated(accepted),
        EmploymentAccepted(
            contract.id,
            employer.session_id,
            worker.session_id,
            development.id,
            2,
            "food",
        ),
    ]


@pytest.mark.parametrize("is_application", [False, True])
def test_completed_employment_becomes_accepted_wage_trade_in_trade_phase(
        make_game, is_application):
    game = make_game(training=False)
    game.start_game()
    employer = game.players["player-1"]
    worker = game.players["player-2"]
    development = owned_development(game, employer)
    employment_initiator = worker if is_application else employer
    employment_target = employer if is_application else worker
    _created, employment = create_contract(game, employment_initiator.session_id, {
        "type": "EMPLOYMENT",
        "target_id": employment_target.session_id,
        "dev_id": development.id,
        "wage": 2,
        "wage_type": "food",
        "is_application": is_application,
    })
    update_contract(game, employment_target.session_id, employment, "ACCEPT")
    job = worker.available_work[0]

    assert game.handle_action(employer.session_id, {
        "action_command": "FINISH_PHASE",
        "payload": {},
    }) is True
    assert game.handle_action(worker.session_id, {
        "action_command": "COMMIT_WORK",
        "payload": {"job": job},
    }) is True

    assert game.phase == "TRADE"
    assert employment.id not in employer.actions
    wage_trades = [
        action for action in employer.actions.values()
        if isinstance(action, TradeContract)
        and getattr(action, "employment_contract_id", None) == employment.id
    ]
    assert len(wage_trades) == 1
    wage_trade = wage_trades[0]
    assert wage_trade.status == "ACCEPTED"
    assert wage_trade.initiator_id == employer.session_id
    assert wage_trade.target_id == worker.session_id
    assert wage_trade.offer_items == {"food": 2}
    assert wage_trade.request_items == {}
    assert wage_trade.reason == "WAGE_PAYMENT"
    assert worker.actions[wage_trade.id] is wage_trade
    employer_state = game.get_state_for_player(employer.session_id)
    serialized_wage_trade = next(
        action for action in employer_state["me"]["actions"]
        if action["id"] == wage_trade.id
    )
    assert serialized_wage_trade["status"] == "ACCEPTED"
    assert serialized_wage_trade["reason"] == "WAGE_PAYMENT"
    json.dumps(employer_state)

    assert game.handle_action(employer.session_id, {
        "action_command": "FINALIZE",
        "payload": {"action_id": wage_trade.id, "actual_items": {}},
    }) is True
    assert game.handle_action(worker.session_id, {
        "action_command": "FINALIZE",
        "payload": {"action_id": wage_trade.id, "actual_items": {}},
    }) is True

    assert worker.trade_history[-1]["reason"] == "WAGE_PAYMENT"
    assert worker.trade_history[-1]["promised_received"] == {"food": 2}
    assert worker.trade_history[-1]["actual_received"] == {}
    assert game.lie_count[employer.session_id] == 1


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


def test_campfire_acceptance_rejects_host_joining_another_fire(make_game):
    game = make_game()
    first_host = game.players["player-1"]
    second_host = game.players["player-2"]
    first_host.fire_status = "HOST"
    second_host.fire_status = "HOST"
    contract = CampfireContract(
        first_host.session_id,
        second_host.session_id,
        is_request=True,
    )
    game.contract_factory._add_contract_to_players(contract)

    status, unchanged = update_contract(
        game,
        second_host.session_id,
        contract,
        "ACCEPT",
    )

    assert status == "ILLEGAL"
    assert unchanged.status == "PENDING"
    assert first_host.fire_status == "HOST"
    assert second_host.fire_guests == []


def test_guest_can_move_from_one_host_fire_to_another(make_game):
    game = make_game(("player-1", "player-2", "player-3"))
    old_host = game.players["player-1"]
    new_host = game.players["player-2"]
    guest = game.players["player-3"]
    old_host.fire_status = "HOST"
    old_host.fire_guests = [guest.session_id]
    new_host.fire_status = "HOST"
    guest.fire_status = "GUEST"
    contract = CampfireContract(
        guest.session_id,
        new_host.session_id,
        is_request=True,
    )
    game.contract_factory._add_contract_to_players(contract)

    status, accepted = update_contract(
        game,
        new_host.session_id,
        contract,
        "ACCEPT",
    )

    assert status == "UPDATED_ACCEPTED"
    assert accepted.status == "ACCEPTED"
    assert old_host.fire_guests == []
    assert new_host.fire_guests == [guest.session_id]
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


def test_barter_denies_original_and_creates_counter_trade(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    _created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {"wood": 1},
    })

    bartered, counter = update_contract(
        game, second.session_id, trade, "BARTER",
        {"offer_items": {"food": 2}, "request_items": {}},
    )

    assert bartered == "CREATED"
    trade = game.contract_factory.find_contract(trade.id)
    assert trade.status == "DENIED"
    assert counter.id != trade.id
    assert counter.initiator_id == second.session_id
    assert counter.target_id == first.session_id
    assert counter.offer_items == {"food": 2}
    assert counter.request_items == {}


def test_cancel_denies_pending_contract(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    _created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {"wood": 1},
    })

    cancelled, trade = update_contract(
        game, first.session_id, trade, "CANCEL",
    )

    assert cancelled == "UPDATED_DENIED"
    assert trade.status == "DENIED"


def test_contract_updates_are_recorded_as_domain_events(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    _created, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {},
    })

    accepted_status, accepted_trade = update_contract(
        game, second.session_id, trade, "ACCEPT")

    event = game.domain_events[-1]
    assert accepted_status == "UPDATED_ACCEPTED"
    assert event == ContractUpdated(accepted_trade)
    assert first.actions[trade.id] is accepted_trade
    assert second.actions[trade.id] is accepted_trade


def test_contract_creation_is_applied_by_state_event(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]

    status, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {},
    })

    assert status == "CREATED"
    assert game.domain_events[-1] == ContractCreated(trade)
    assert first.actions[trade.id] is trade
    assert second.actions[trade.id] is trade


def test_contract_cleanup_removes_and_expires_through_state_events(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    _created_trade, trade = create_contract(game, first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {},
    })
    development = owned_development(game, first)
    _created_employment, employment = create_contract(game, first.session_id, {
        "type": "EMPLOYMENT",
        "target_id": second.session_id,
        "dev_id": development.id,
        "wage": 1,
        "wage_type": "food",
    })

    game.contract_factory.cleanup_end_of_phase()

    assert trade.status == "EXPIRED"
    assert trade.waiting_on_id is None
    assert employment.id not in first.actions
    assert employment.id not in second.actions
    assert ContractExpired(trade.id) in game.domain_events
    assert ContractRemoved(employment.id) in game.domain_events


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
