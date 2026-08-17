from service.game.models.development import Development
from service.game.models.map import MapTile
from service.game.state.developments import DevelopmentState
from service.game.state.events import (
    ContractExpired,
    ContractUpdated,
    DevelopmentContestActivated,
    DevelopmentContestCleared,
    DevelopmentOwnershipTransferred,
    DevelopmentUpgraded,
    PlayerResourcesGained,
)
from service.game.state.phase_resolution import WORK_RESOLUTION_ORDER


def place_development(
        game, owner_id="player-1", dev_id="farm-1", dev_type="Farm",
        tile_id="tile-1"):
    tile = MapTile(tile_id, 0, 0, dev_type)
    development = Development(
        dev_id,
        dev_type,
        owner_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    development.level = 2
    tile.development = development
    game.map_data[tile.id] = tile
    game.players[owner_id].developments = [development.id]
    return development


def work_payload(development, action_id=None):
    return {
        "job": {
            "development": development.to_dict(),
            "wage": development.level,
            "wage_type": "food",
            "employer_id": development.owner,
            "action_id": action_id,
        }
    }


def contest(game, player_id, development, side):
    return game.handle_action(player_id, {
        "action_command": "CONTEST_DEV",
        "payload": {"dev_id": development.id, "side": side},
    })


def test_same_phase_contest_invalidates_upgrade_and_work_intents_and_extends_timer(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3", "player-4"))
    game.start_game()
    development = place_development(game)
    owner = game.players["player-1"]
    owner.resources = {"food": 20, "wood": 20, "iron": 20}
    game.start_phase("WORK")
    original_phase_end = game.phase_end_time

    assert game.handle_action("player-1", {
        "action_command": "UPGRADE_DEV",
        "payload": {"dev_id": development.id},
    }) is True
    assert game.handle_action("player-2", {
        "action_command": "COMMIT_WORK",
        "payload": work_payload(development),
    }) is True
    assert game.handle_action("player-3", {
        "action_command": "COMMIT_WORK",
        "payload": work_payload(development),
    }) is True

    assert game.handle_action("player-4", {
        "action_command": "CONTEST_DEV",
        "payload": {"dev_id": development.id, "side": "INITIATOR"},
    }) is True

    assert development.is_contested is True
    assert development.state == DevelopmentState.CONTESTED.value
    assert development.to_dict()["state"] == DevelopmentState.CONTESTED.value
    assert development.pending_contest is False
    assert game.phase_end_time > original_phase_end
    assert game.get_intent("player-1") is None
    assert game.get_intent("player-2") is None
    assert game.get_intent("player-3") is None
    assert owner.finished_phase is False
    assert game.players["player-2"].finished_phase is False
    assert game.players["player-3"].finished_phase is False
    assert any(
        note["reason"] == "development_contested"
        for note in game.drain_notifications("player-2")
    )
    assert DevelopmentContestActivated(
        development.id,
        "player-4",
    ) in game.domain_events


def test_tied_same_phase_contest_remains_active_until_following_work_phase(make_game, monkeypatch):
    game = make_game(player_ids=("player-1", "player-2", "player-3", "player-4"))
    game.start_game()
    development = place_development(game)
    game.start_phase("WORK")
    contest(game, "player-4", development, "INITIATOR")

    assert contest(game, "player-1", development, "OWNER") is True
    assert contest(game, "player-2", development, "OWNER") is True
    assert contest(game, "player-3", development, "CONTESTER") is True
    assert contest(game, "player-4", development, "CONTESTER") is True

    assert game.phase == "TRADE"
    assert development.is_contested is True
    assert development.owner == "player-1"

    game.next_phase()
    assert game.phase == "NIGHT"
    for player in game.players.values():
        player.resources["food"] = 5
        player.fire_status = "HOST"
    monkeypatch.setattr(
        "service.game.models.player.random.random", lambda: 1.0)
    game.next_phase()

    assert game.phase == "WORK"
    assert development.is_contested is True
    assert development.owner == "player-1"


def test_upgrade_intent_resolves_before_workers_produce_resources(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3"))
    game.start_game()
    development = place_development(game)
    owner = game.players["player-1"]
    owner.resources = {"food": 0, "wood": 20, "iron": 20}
    game.start_phase("WORK")

    assert game.handle_action("player-1", {
        "action_command": "UPGRADE_DEV",
        "payload": {"dev_id": development.id},
    }) is True
    assert game.handle_action("player-2", {
        "action_command": "COMMIT_WORK",
        "payload": work_payload(development),
    }) is True
    assert game.handle_action("player-3", {
        "action_command": "COMMIT_WORK",
        "payload": work_payload(development),
    }) is True

    game.next_phase()

    assert development.level == 3
    assert owner.resources["food"] == 6


def test_owner_group_winning_contest_resolves_without_transfer(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3", "player-4"))
    game.start_game()
    development = place_development(game)
    game.start_phase("WORK")
    contest(game, "player-4", development, "INITIATOR")

    contest(game, "player-1", development, "OWNER")
    contest(game, "player-2", development, "OWNER")
    contest(game, "player-3", development, "OWNER")
    contest(game, "player-4", development, "CONTESTER")

    game.next_phase()

    assert development.is_contested is False
    assert development.state == DevelopmentState.STABLE.value
    assert development.contest_initiator_id is None
    assert development.owner == "player-1"
    assert development.id in game.players["player-1"].developments
    assert development.id not in game.players["player-4"].developments
    assert game.domain_events[-1] == DevelopmentContestCleared(development.id)


def test_contender_group_winning_contest_transfers_ownership(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3", "player-4"))
    game.start_game()
    development = place_development(game)
    game.start_phase("WORK")
    contest(game, "player-4", development, "INITIATOR")

    contest(game, "player-1", development, "OWNER")
    contest(game, "player-2", development, "CONTESTER")
    contest(game, "player-3", development, "CONTESTER")
    contest(game, "player-4", development, "CONTESTER")

    game.next_phase()

    assert development.is_contested is False
    assert development.contest_initiator_id is None
    assert development.owner == "player-4"
    assert development.id not in game.players["player-1"].developments
    assert development.id in game.players["player-4"].developments
    assert game.domain_events[-2:] == [
        DevelopmentOwnershipTransferred(
            development.id,
            "player-1",
            "player-4",
        ),
        DevelopmentContestCleared(development.id),
    ]


def test_developments_are_derived_from_map_tiles_not_a_second_store(make_game):
    game = make_game(player_ids=("player-1",))
    development = place_development(game)

    assert game.developments == {development.id: development}
    assert game.map_data["tile-1"].development is development

    game.developments.pop(development.id)

    assert game.developments == {}
    assert game.map_data["tile-1"].development is None


def test_work_resolution_order_is_explicit_and_deterministic(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3"))
    game.start_game()
    contested = place_development(game, dev_id="farm-1", tile_id="tile-1")
    work_dev = place_development(
        game, dev_id="woods-1", dev_type="Woods", tile_id="tile-2")
    owner = game.players["player-1"]
    worker = game.players["player-3"]
    owner.resources["food"] = 20
    owner.resources["wood"] = 0
    owner.resources["iron"] = 20
    _created, contract = game.contract_factory.process_contract(
        owner.session_id,
        {
            "type": "TRADE",
            "target_id": worker.session_id,
            "offer_items": {"food": 1},
            "request_items": {},
        },
    )
    game.start_phase("WORK")
    game.handle_action("player-1", {
        "action_command": "UPGRADE_DEV",
        "payload": {"dev_id": work_dev.id},
    })
    contest(game, "player-2", contested, "INITIATOR")
    contest(game, "player-2", contested, "CONTESTER")
    game.handle_action("player-3", {
        "action_command": "COMMIT_WORK",
        "payload": work_payload(work_dev),
    })

    game.next_phase()

    event_types = [type(event) for event in game.domain_events]
    assert WORK_RESOLUTION_ORDER == (
        "resolve_development_intents",
        "resolve_work_intents",
        "resolve_contests",
        "cleanup_contracts",
    )
    assert event_types.index(DevelopmentUpgraded) < event_types.index(
        PlayerResourcesGained)
    assert event_types.index(PlayerResourcesGained) < event_types.index(
        DevelopmentOwnershipTransferred)
    assert event_types.index(DevelopmentOwnershipTransferred) < event_types.index(
        ContractExpired)
    assert contract.status == "EXPIRED"
