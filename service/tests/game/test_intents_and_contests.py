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
from service.game.state.intents import ContestIntent, WorkIntent
from service.game.state.player_phase import PlayerPhaseState


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


def test_worker_can_replace_invalidated_work_with_contest_support(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3", "player-4"))
    game.start_game()
    development = place_development(game)
    game.start_phase("WORK")

    assert game.handle_action("player-2", {
        "action_command": "COMMIT_WORK",
        "payload": work_payload(development),
    }) is True
    assert contest(game, "player-4", development, "INITIATOR") is True
    assert game.get_intent("player-2") is None
    assert (
        game.players["player-2"].phase_state
        == PlayerPhaseState.NEEDS_REPLACEMENT.value
    )

    assert contest(game, "player-2", development, "OWNER") is True

    replacement = game.get_intent("player-2")
    assert isinstance(replacement, ContestIntent)
    assert replacement.development_id == development.id
    assert replacement.side == "OWNER"
    assert (
        game.players["player-2"].phase_state
        == PlayerPhaseState.INTENT_SUBMITTED.value
    )


def test_worker_can_replace_invalidated_work_with_a_different_job(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3", "player-4"))
    game.start_game()
    contested = place_development(
        game, owner_id="player-1", dev_id="farm-1", tile_id="tile-1")
    replacement_development = place_development(
        game, owner_id="player-3", dev_id="woods-1", dev_type="Woods",
        tile_id="tile-2")
    game.start_phase("WORK")

    assert game.handle_action("player-2", {
        "action_command": "COMMIT_WORK",
        "payload": work_payload(contested),
    }) is True
    assert contest(game, "player-4", contested, "INITIATOR") is True
    assert game.get_intent("player-2") is None
    assert (
        game.players["player-2"].phase_state
        == PlayerPhaseState.NEEDS_REPLACEMENT.value
    )

    assert game.handle_action("player-2", {
        "action_command": "COMMIT_WORK",
        "payload": work_payload(replacement_development),
    }) is True

    replacement = game.get_intent("player-2")
    assert isinstance(replacement, WorkIntent)
    assert replacement.development_id == replacement_development.id
    assert replacement.job["development"]["id"] == replacement_development.id
    assert (
        game.players["player-2"].phase_state
        == PlayerPhaseState.RESOLVED.value
    )


def test_player_cannot_initiate_a_second_active_contest(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3"))
    game.start_game()
    first = place_development(
        game, owner_id="player-1", dev_id="farm-1", tile_id="tile-1")
    second = place_development(
        game, owner_id="player-2", dev_id="farm-2", tile_id="tile-2")
    game.start_phase("WORK")

    assert contest(game, "player-3", first, "INITIATOR") is True
    assert contest(game, "player-3", second, "INITIATOR") is False
    assert first.is_contested is True
    assert second.is_contested is False


def test_initiating_a_contest_commits_the_players_work_action(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    development = place_development(game, owner_id="player-1")
    attacker = game.players["player-2"]
    attacker.resources = {"food": 20, "wood": 20, "iron": 20}
    game.start_phase("WORK")

    assert contest(game, attacker.session_id, development, "INITIATOR") is True

    intent = game.get_intent(attacker.session_id)
    assert isinstance(intent, ContestIntent)
    assert intent.development_id == development.id
    assert intent.side == "CONTESTER"
    assert attacker.finished_phase is True

    buildable_tile = next(
        tile for tile in game.map_data.values()
        if tile.development is None and tile.type in game.development_costs
    )
    assert game.handle_action(attacker.session_id, {
        "action_command": "BUILD_DEV",
        "payload": {"tile_id": buildable_tile.id},
    }) is False


def test_player_cannot_initiate_a_contest_after_committing_work(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    development = place_development(game, owner_id="player-1")
    attacker = game.players["player-2"]
    attacker.resources = {"food": 20, "wood": 20, "iron": 20}
    game.start_phase("WORK")
    buildable_tile = next(
        tile for tile in game.map_data.values()
        if tile.development is None and tile.type in game.development_costs
    )

    assert game.handle_action(attacker.session_id, {
        "action_command": "BUILD_DEV",
        "payload": {"tile_id": buildable_tile.id},
    }) is True
    assert attacker.finished_phase is True
    assert contest(game, attacker.session_id, development, "INITIATOR") is False
    assert development.is_contested is False


def test_legal_actions_offer_no_new_initiations_during_an_active_contest(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3"))
    game.start_game()
    first = place_development(
        game, owner_id="player-1", dev_id="farm-1", tile_id="tile-1")
    place_development(
        game, owner_id="player-2", dev_id="farm-2", tile_id="tile-2")
    game.start_phase("WORK")
    contest(game, "player-3", first, "INITIATOR")

    contest_actions = [
        action for action in game.get_legal_actions("player-3")
        if action["action_command"] == "CONTEST_DEV"
    ]

    assert contest_actions == [{
        "action_command": "CONTEST_DEV",
        "payload": {"dev_id": "farm-1", "side": "CONTESTER"},
    }]


def test_tied_same_phase_contest_remains_active_until_following_work_phase(make_game, monkeypatch):
    game = make_game(player_ids=("player-1", "player-2", "player-3", "player-4"))
    game.start_game()
    development = place_development(game)
    game.start_phase("WORK")
    contest(game, "player-4", development, "INITIATOR")

    assert contest(game, "player-1", development, "OWNER") is True
    assert contest(game, "player-2", development, "OWNER") is True
    assert contest(game, "player-3", development, "CONTESTER") is True

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
