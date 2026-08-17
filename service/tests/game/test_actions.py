from service.game.packet_handling.base import FinishPhaseCommand
from service.game.packet_handling.campfire import StartFireCommand
from service.game.packet_handling.development import (
    MaintainDevelopmentCommand,
    UpgradeDevelopmentCommand,
)
from service.game.packet_handling.work import resolve_work_phase
from service.game.models.development import Development
from service.game.models.map import MapTile
from service.game.state.events import (
    DevelopmentBuilt,
    DevelopmentMaintained,
    DevelopmentUpgraded,
    FireStarted,
    PlayerResourcesSpent,
)
from service.game.state.intents import MaintainIntent


def make_development(game, owner_id="player-1", dev_id="dev-1", dev_type="Farm"):
    development = Development(
        dev_id,
        dev_type,
        owner_id,
        game.rules.MAX_DEVELOPMENT_LEVEL,
        game.rules.MAINTENANCE_DAYS,
        game.rules.RESOURCE_COSTS,
    )
    game.developments[dev_id] = development
    game.players[owner_id].developments.append(dev_id)
    return development


def test_build_action_deducts_cost_and_assigns_development(make_game):
    game = make_game()
    game.start_game()
    player = game.players["player-1"]
    tile = MapTile("farm-tile", 0, 0, "Farm")
    game.map_data = {tile.id: tile}
    starting_wood = player.resources["wood"]

    accepted = game.handle_action("player-1", {
        "action_command": "BUILD_DEV",
        "payload": {"tile_id": tile.id},
    })

    assert accepted is True
    assert player.resources["wood"] == starting_wood - 2
    assert len(player.developments) == 1
    assert tile.development.id == player.developments[0]
    assert tile.development.owner == player.session_id
    assert player.finished_phase is True


def test_build_action_records_authoritative_domain_events(make_game):
    game = make_game()
    game.start_game()
    player = game.players["player-1"]
    tile = MapTile("farm-tile", 0, 0, "Farm")
    game.map_data = {tile.id: tile}

    accepted = game.handle_action("player-1", {
        "action_command": "BUILD_DEV",
        "payload": {"tile_id": tile.id},
    })

    assert accepted is True
    assert game.domain_events[-3:-1] == [
        PlayerResourcesSpent(player.session_id, {"wood": 2}),
        DevelopmentBuilt(
            tile.development.id,
            tile.id,
            player.session_id,
            "Farm",
        ),
    ]


def test_build_action_rejects_occupied_tile_without_spending_resources(make_game):
    game = make_game()
    game.start_game()
    player = game.players["player-1"]
    tile = MapTile("farm-tile", 0, 0, "Farm")
    tile.development = object()
    game.map_data = {tile.id: tile}
    starting_resources = player.resources.copy()

    accepted = game.handle_action("player-1", {
        "action_command": "BUILD_DEV",
        "payload": {"tile_id": tile.id},
    })

    assert accepted is False
    assert player.resources == starting_resources
    assert player.finished_phase is False


def test_maintenance_and_upgrade_apply_dynamic_costs(make_game):
    game = make_game()
    game.phase = "WORK"
    player = game.players["player-1"]
    player.resources = {"food": 20, "wood": 20, "iron": 20}
    development = make_development(game)
    development.maintenance_days = 1

    maintained = MaintainDevelopmentCommand(player.session_id, {
        "dev_id": development.id
    }).execute(game, player)
    assert maintained is True
    assert development.maintenance_days == 1
    assert isinstance(game.get_intent(player.session_id), MaintainIntent)

    resolve_work_phase(game)
    assert development.maintenance_days == game.rules.MAINTENANCE_DAYS

    development.maintenance_days = 1
    previous_level = development.level
    upgraded = UpgradeDevelopmentCommand(player.session_id, {
        "dev_id": development.id
    }).execute(game, player)

    assert upgraded is True
    assert development.level == previous_level
    assert game.get_intent(player.session_id).development_id == development.id

    resolve_work_phase(game)

    assert development.level == previous_level + 1


def test_maintenance_resolution_records_authoritative_domain_events(make_game):
    game = make_game()
    game.phase = "WORK"
    player = game.players["player-1"]
    player.resources = {"food": 20, "wood": 20, "iron": 20}
    development = make_development(game)
    development.maintenance_days = 1

    accepted = MaintainDevelopmentCommand(player.session_id, {
        "dev_id": development.id,
    }).execute(game, player)

    assert accepted is True
    assert game.domain_events == []

    resolve_work_phase(game)

    assert game.domain_events[-2:] == [
        PlayerResourcesSpent(
            player.session_id, development.get_maintenance_cost()),
        DevelopmentMaintained(development.id),
    ]


def test_upgrade_resolution_records_authoritative_domain_events(make_game):
    game = make_game()
    game.phase = "WORK"
    player = game.players["player-1"]
    player.resources = {"food": 20, "wood": 20, "iron": 20}
    development = make_development(game)
    upgrade_cost = development.get_upgrade_cost()

    accepted = UpgradeDevelopmentCommand(player.session_id, {
        "dev_id": development.id,
    }).execute(game, player)
    resolve_work_phase(game)

    assert accepted is True
    assert game.domain_events[-2:] == [
        PlayerResourcesSpent(player.session_id, upgrade_cost),
        DevelopmentUpgraded(development.id),
    ]


def test_maintenance_and_upgrade_require_work_phase_and_owner(make_game):
    game = make_game()
    owner = game.players["player-1"]
    other = game.players["player-2"]
    owner.resources = {"food": 20, "wood": 20, "iron": 20}
    other.resources = {"food": 20, "wood": 20, "iron": 20}
    development = make_development(game)
    before = development.maintenance_days
    game.phase = "TRADE"

    assert MaintainDevelopmentCommand(owner.session_id, {
        "dev_id": development.id,
    }).execute(game, owner) is False
    game.phase = "WORK"
    assert MaintainDevelopmentCommand(other.session_id, {
        "dev_id": development.id,
    }).execute(game, other) is False
    assert UpgradeDevelopmentCommand(other.session_id, {
        "dev_id": development.id,
    }).execute(game, other) is False
    assert development.maintenance_days == before


def test_upgrade_uses_ruleset_maximum(make_game):
    game = make_game(ruleset="wealthy")
    game.phase = "WORK"
    owner = game.players["player-1"]
    owner.resources = {"food": 20, "wood": 20, "iron": 20}
    development = make_development(game)
    development.level = 3

    accepted = UpgradeDevelopmentCommand(owner.session_id, {
        "dev_id": development.id,
    }).execute(game, owner)

    assert accepted is True
    assert development.level == 3

    resolve_work_phase(game)

    assert development.level == 4


def test_running_game_cannot_be_restarted(make_game):
    game = make_game()

    assert game.status == "RUNNING"
    original_map = game.map_data
    original_length = game.game_length
    assert game.start_game() is False
    assert game.map_data is original_map
    assert game.game_length == original_length


def test_start_fire_requires_night_and_consumes_wood(make_game):
    game = make_game()
    player = game.players["player-1"]
    starting_wood = player.resources["wood"]

    rejected = StartFireCommand(player.session_id, {}).execute(game, player)
    game.phase = "NIGHT"
    accepted = StartFireCommand(player.session_id, {}).execute(game, player)

    assert rejected is False
    assert accepted is True
    assert player.fire_status == "HOST"
    assert player.resources["wood"] == starting_wood - 1


def test_start_fire_records_authoritative_domain_events(make_game):
    game = make_game()
    game.phase = "NIGHT"
    player = game.players["player-1"]

    accepted = StartFireCommand(player.session_id, {}).execute(game, player)

    assert accepted is True
    assert game.domain_events[-2:] == [
        PlayerResourcesSpent(player.session_id, {"wood": 1}),
        FireStarted(player.session_id),
    ]


def test_finish_phase_marks_player_finished(make_game):
    game = make_game()
    player = game.players["player-1"]

    accepted = FinishPhaseCommand(player.session_id, {}).execute(game, player)

    assert accepted is True
    assert player.finished_phase is True
