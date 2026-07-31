from service.game.actions.conflict import resolve_contests
from service.game.actions.dispatcher import ActionDispatcher
from service.game.actions.phase_resolution import PhaseResolver
from service.game.actions.work import resolve_work_phase, start_work_phase
from service.game.models.development import Development


def test_training_trade_resolution_preserves_trade_history(make_game):
    game = make_game(training=True)
    player = game.players["player-1"]
    player.trade_history = [{"id": "trade-1"}]

    PhaseResolver.resolve_trade(game)

    assert player.trade_history == [{"id": "trade-1"}]


def test_non_training_trade_resolution_rotates_trade_history(make_game):
    game = make_game(training=False)
    player = game.players["player-1"]
    player.trade_history = [{"id": "trade-1"}]

    PhaseResolver.resolve_trade(game)

    assert player.old_history == [{"id": "trade-1"}]
    assert player.trade_history == []


def test_work_phase_production_goes_to_development_owner(make_game):
    game = make_game()
    owner = game.players["player-1"]
    worker = game.players["player-2"]
    owner.resources["food"] = 0
    worker.committed_action = {
        "development": {
            "id": "dev-1",
            "owner_id": owner.session_id,
            "type": "Farm",
            "level": 2,
        }
    }

    resolve_work_phase(game)

    assert owner.resources["food"] == 2
    assert worker.resources["food"] == game.starting_inventory["food"]
    assert owner.timeline[-1]["type"] == "LABOR_EXPLOITED"


def test_start_work_phase_only_exposes_uncontested_owner_jobs(make_game):
    game = make_game()
    game.status = "RUNNING"
    owner = game.players["player-1"]
    available = Development(
        "dev-1", "Farm", owner.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    contested = Development(
        "dev-2", "Woods", owner.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    contested.is_contested = True
    game.developments = {available.id: available, contested.id: contested}

    start_work_phase(game)

    assert [job["development"]["id"] for job in owner.available_work] == ["dev-1"]


def test_contest_resolution_transfers_development_when_owner_is_absent(make_game):
    game = make_game()
    owner = game.players["player-1"]
    attacker = game.players["player-2"]
    development = Development(
        "dev-1", "Farm", owner.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    development.is_contested = True
    development.contest_initiator_id = attacker.session_id
    owner.developments.append(development.id)
    attacker.committed_action = {
        "type": "CONTEST_ACTION",
        "dev_id": development.id,
        "side": "CONTESTER",
    }
    game.developments = {development.id: development}

    resolve_contests(game)

    assert development.owner == attacker.session_id
    assert development.id not in owner.developments
    assert development.id in attacker.developments
    assert development.is_contested is False


def test_night_resolution_consumes_food_resets_fire_and_degrades_assets(make_game, monkeypatch):
    game = make_game()
    game.status = "RUNNING"
    game.day = 1
    game.game_length = 10
    player = game.players["player-1"]
    player.resources.update({"food": 2, "wood": 2, "iron": 0})
    player.fire_status = "HOST"
    development = Development(
        "dev-1", "Farm", player.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    game.developments = {development.id: development}
    starting_maintenance = development.maintenance_days
    monkeypatch.setattr(
        "service.game.models.player.random.random", lambda: 1.0)

    ActionDispatcher.resolve_night(game)

    assert player.resources["food"] == 1
    assert player.fire_status == "COLD"
    assert player.health == "healthy"
    assert development.maintenance_days == starting_maintenance - 1


def test_night_resolution_removes_multiple_degraded_developments(make_game, monkeypatch):
    game = make_game()
    owner = game.players["player-1"]
    developments = [
        Development(
            f"dev-{index}", "Farm", owner.session_id,
            game.rules.MAX_DEVELOPMENT_LEVEL,
            game.rules.MAINTENANCE_DAYS,
            game.rules.RESOURCE_COSTS,
        )
        for index in range(2)
    ]
    game.developments = {item.id: item for item in developments}
    owner.developments = [item.id for item in developments]
    for development in developments:
        monkeypatch.setattr(development, "degrade", lambda: False)

    PhaseResolver.resolve_night(game)

    assert game.developments == {}
    assert owner.developments == []


def test_end_of_work_phase_expires_pending_contracts(make_game):
    game = make_game()
    first = game.players["player-1"]
    second = game.players["player-2"]
    status, contract = game.contract_factory.process_contract(first.session_id, {
        "type": "TRADE",
        "target_id": second.session_id,
        "offer_items": {"food": 1},
        "request_items": {},
    })
    assert status == "CREATED"

    ActionDispatcher.resolve_work_phase(game)

    assert contract.status == "EXPIRED"
    assert contract.waiting_on_id is None
