from service.game.state.projections import (
    build_phase_projection,
    build_trade_projection,
    build_work_projection,
)


def test_work_projection_exposes_bot_decision_inputs(make_game):
    game = make_game(player_ids=("player-1", "player-2"))
    game.start_game()
    player = game.players["player-1"]
    player.available_work = [{
        "development": {"id": "farm-1", "type": "Farm"},
        "wage": 2,
        "wage_type": "food",
        "employer_id": "player-2",
    }]

    projection = build_work_projection(game, player.session_id)

    assert projection["phase"] == "WORK"
    assert projection["phase_state"] == "ACTIVE"
    assert projection["finished_phase"] is False
    assert projection["available_work"][0]["development"]["id"] == "farm-1"
    assert "COMMIT_WORK" in {
        action["action_command"] for action in projection["legal_actions"]
    }


def test_locked_work_projection_is_derived_from_player_phase_state(make_game):
    game = make_game()
    game.start_game()
    player = game.players["player-1"]
    player.finished_phase = True

    projection = build_work_projection(game, player.session_id)

    assert projection["phase_state"] == "RESOLVED"
    assert projection["finished_phase"] is True
    assert "COMMIT_WORK" not in {
        action["action_command"] for action in projection["legal_actions"]
    }


def test_phase_projection_selects_current_phase_projection(make_game):
    game = make_game()
    game.start_game()
    game.start_phase("TRADE")

    projection = build_phase_projection(game, "player-1")

    assert projection == build_trade_projection(game, "player-1")
    assert projection["phase"] == "TRADE"
    assert "legal_actions" in projection
