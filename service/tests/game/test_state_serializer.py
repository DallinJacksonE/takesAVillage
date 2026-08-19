import types

from service.game.serializers.state import build_player_state
from service.game.packet_handling.contracts import TradeContract
from service.game.state.intents import WorkIntent


def test_player_list_exposes_public_state_but_keeps_private_state_in_me(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()

    state = build_player_state(game, "player-1")

    assert "resources" in state["me"]
    other = next(player for player in state["player_list"] if player["id"] == "player-2")
    assert set(other) == {
        "id",
        "name",
        "health",
        "fire_status",
        "fire_guests",
        "developments",
        "finished_phase",
        "phase_state",
        "visual_state",
        "reaction",
    }
    assert "resources" not in other
    assert "actions" not in other
    assert "timeline" not in other


def test_player_reaction_is_public_until_its_authoritative_expiry(make_game):
    now = [100.0]
    game = make_game(training=False)
    game._clock = lambda: now[0]
    game.start_game()

    assert game.handle_action("player-1", {
        "action_command": "SET_EMOJI",
        "payload": {"emoji": "👍"},
    }) is True
    assert game.players["player-1"].phase_state == "ACTIVE"

    state = build_player_state(game, "player-2")
    reacting = next(
        player for player in state["player_list"] if player["id"] == "player-1"
    )
    assert reacting["reaction"] == {"emoji": "👍", "expires_at": 104.0}

    now[0] = 104.0
    expired_state = build_player_state(game, "player-2")
    expired = next(
        player for player in expired_state["player_list"]
        if player["id"] == "player-1"
    )
    assert expired["reaction"] is None


def test_player_can_react_after_submitting_a_phase_action(make_game):
    game = make_game(training=False)
    game.start_game()
    game.players["player-1"].submit_phase_intent()

    assert game.handle_action("player-1", {
        "action_command": "SET_EMOJI",
        "payload": {"emoji": "❤️"},
    }) is True


def test_player_reaction_rejects_unapproved_content(make_game):
    game = make_game(training=False)
    game.start_game()

    assert game.handle_action("player-1", {
        "action_command": "SET_EMOJI",
        "payload": {"emoji": "<script>"},
    }) is False
    assert game.players["player-1"].reaction is None


def test_work_intent_projects_public_animation_and_location(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    game.developments["mine-1"] = types.SimpleNamespace(
        type="Mine",
        to_dict=lambda: {"id": "mine-1", "type": "Mine"},
    )
    game.set_intent(WorkIntent(
        player_id="player-2",
        development_id="mine-1",
        job={"development": {"id": "mine-1", "type": "Mine"}},
    ))

    state = build_player_state(game, "player-1")
    worker = next(player for player in state["player_list"] if player["id"] == "player-2")

    assert worker["visual_state"] == {
        "animation": "WORK_MINE",
        "location": {"kind": "DEVELOPMENT", "id": "mine-1"},
    }


def test_health_overrides_work_animation(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    game.players["player-2"].health = "sick"
    game.developments["farm-1"] = types.SimpleNamespace(
        type="Farm",
        to_dict=lambda: {"id": "farm-1", "type": "Farm"},
    )
    game.set_intent(WorkIntent(
        player_id="player-2",
        development_id="farm-1",
        job={"development": {"id": "farm-1", "type": "Farm"}},
    ))

    state = build_player_state(game, "player-1")
    worker = next(player for player in state["player_list"] if player["id"] == "player-2")

    assert worker["visual_state"] == {
        "animation": "SICK",
        "location": {"kind": "HOME"},
    }


def test_completed_build_projects_hammer_animation_at_tile(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    game.players["player-2"].committed_action = {
        "Action": "Build",
        "Tile_Id": "tile-4",
    }

    state = build_player_state(game, "player-1")
    builder = next(player for player in state["player_list"] if player["id"] == "player-2")

    assert builder["visual_state"] == {
        "animation": "BUILD",
        "location": {"kind": "TILE", "id": "tile-4"},
    }


def test_accepted_trade_projects_both_players_carrying_at_shared_trade(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    game.phase = "TRADE"
    trade = TradeContract("player-1", "player-2", {"food": 1}, {"wood": 1})
    trade.status = "ACCEPTED"
    game.players["player-1"].actions[trade.id] = trade
    game.players["player-2"].actions[trade.id] = trade

    state = build_player_state(game, "player-1")

    visuals = {
        player["id"]: player["visual_state"]
        for player in state["player_list"]
    }
    assert visuals == {
        "player-1": {
            "animation": "CARRY",
            "location": {
                "kind": "TRADE",
                "id": trade.id,
                "side": "INITIATOR",
            },
        },
        "player-2": {
            "animation": "CARRY",
            "location": {
                "kind": "TRADE",
                "id": trade.id,
                "side": "TARGET",
            },
        },
    }


def test_finalized_trade_returns_players_home_to_idle(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    game.phase = "TRADE"
    trade = TradeContract("player-1", "player-2", {"food": 1}, {"wood": 1})
    trade.status = "FINALIZED"
    trade.initiator_finalized = True
    trade.target_finalized = True
    game.players["player-1"].actions[trade.id] = trade
    game.players["player-2"].actions[trade.id] = trade

    state = build_player_state(game, "player-1")

    assert all(
        player["visual_state"] == {
            "animation": "IDLE",
            "location": {"kind": "HOME"},
        }
        for player in state["player_list"]
    )


def test_night_players_are_grouped_at_host_fires_and_in_the_cold(make_game):
    game = make_game(player_ids=("player-1", "player-2", "player-3"))
    game.start_game()
    game.phase = "NIGHT"
    host = game.players["player-1"]
    guest = game.players["player-2"]
    host.fire_status = "HOST"
    host.fire_guests = [guest.session_id]
    guest.fire_status = "GUEST"
    guest.fire_history = [{"host_id": host.session_id, "role": "guest"}]

    state = build_player_state(game, "player-1")
    visuals = {
        player["id"]: player["visual_state"]
        for player in state["player_list"]
    }

    assert visuals["player-1"]["location"] == {
        "kind": "FIRE", "id": "player-1", "slot": 0,
    }
    assert visuals["player-2"]["location"] == {
        "kind": "FIRE", "id": "player-1", "slot": 1,
    }
    assert visuals["player-3"]["location"] == {
        "kind": "NIGHT_COLD", "slot": 0,
    }


def test_pending_night_transition_projects_hurt_at_preserved_fire_location(make_game):
    game = make_game(player_ids=("player-1", "player-2"), training=False)
    game.start_game()
    game.phase = "NIGHT"
    game.night_transition = {
        "id": "night-1",
        "deadline": 105.0,
        "affected_player_ids": ["player-2"],
        "acknowledged_player_ids": set(),
        "visuals": {
            "player-2": {
                "animation": "HURT",
                "location": {"kind": "FIRE", "id": "player-1", "slot": 1},
            },
        },
    }

    state = build_player_state(game, "player-2")
    affected = next(
        player for player in state["player_list"] if player["id"] == "player-2"
    )

    assert affected["visual_state"] == {
        "animation": "HURT",
        "location": {"kind": "FIRE", "id": "player-1", "slot": 1},
    }
    assert state["night_transition"] == {
        "id": "night-1",
        "deadline": 105.0,
        "affected_player_ids": ["player-2"],
    }
