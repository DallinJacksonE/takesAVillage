from service.game.packet_handling.conflict import resolve_contests
from service.game.packet_handling.dispatcher import PacketDispatcher
from service.game.packet_handling.phase_resolution import PhaseResolver
from service.game.packet_handling.work import resolve_work_phase, start_work_phase
from service.game.models.development import Development
from service.game.models.map import MapTile
from service.game.state.events import (
    ContractExpired,
    DevelopmentDegraded,
    DevelopmentDestroyed,
    GameEnded,
    PlayerDailyNeedsConsumed,
    PlayerResourcesGained,
)
from service.game.state.intents import ContestIntent, WorkIntent


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
    assert game.domain_events[-1] == PlayerResourcesGained(
        owner.session_id, {"food": 2})


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
    game.set_intent(ContestIntent(
        attacker.session_id, development.id, "CONTESTER"))
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

    PacketDispatcher.resolve_night(game)

    assert player.resources["food"] == 1
    assert player.fire_status == "COLD"
    assert player.health == "healthy"
    assert development.maintenance_days == starting_maintenance - 1
    assert PlayerDailyNeedsConsumed(player.session_id) in game.domain_events
    assert DevelopmentDegraded(development.id) in game.domain_events


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
    assert [
        event for event in game.domain_events
        if isinstance(event, DevelopmentDestroyed)
    ] == [
        DevelopmentDestroyed(development.id, owner.session_id)
        for development in developments
    ]


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

    PacketDispatcher.resolve_work_phase(game)

    assert contract.status == "EXPIRED"
    assert contract.waiting_on_id is None
    assert game.domain_events[-1] == ContractExpired(contract.id)


def test_night_resolution_ends_game_through_state_event(make_game):
    game = make_game()
    game.day = game.game_length

    PhaseResolver.resolve_night(game)

    assert game.status == "ENDED"
    assert game.domain_events[-1] == GameEnded()


def test_work_timeout_assigns_default_work_intent_to_highest_level_development(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    owner = game.players["player-1"]
    lower_tile = MapTile("tile-low", 0, 0, "Farm")
    higher_tile = MapTile("tile-high", 1, 0, "Woods")
    lower = Development(
        "dev-low", "Farm", owner.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    higher = Development(
        "dev-high", "Woods", owner.session_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    lower.level = 1
    higher.level = 3
    lower_tile.development = lower
    higher_tile.development = higher
    game.map_data[lower_tile.id] = lower_tile
    game.map_data[higher_tile.id] = higher_tile
    owner.developments = [lower.id, higher.id]
    owner.resources["wood"] = 0
    game.phase_end_time = 0

    game.check_timer()

    assert owner.resources["wood"] == 3
    assert game.phase == "TRADE"


def test_work_timeout_does_not_override_existing_intent(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    lower = Development(
        "dev-low", "Farm", "player-1",
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    higher = Development(
        "dev-high", "Woods", "player-1",
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    lower.level = 1
    higher.level = 3
    game.developments = {lower.id: lower, higher.id: higher}
    player = game.players["player-1"]
    player.resources["food"] = 0
    player.resources["wood"] = 0
    chosen = WorkIntent(
        "player-1", lower.id,
        {"development": lower.to_dict()},
    )
    game.set_intent(chosen)
    game.phase_end_time = 0

    game.check_timer()

    assert player.resources["food"] == 1
    assert player.resources["wood"] == 0
