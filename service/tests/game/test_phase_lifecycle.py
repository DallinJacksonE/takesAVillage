def test_game_starts_in_work_phase_with_generated_map(make_game):
    game = make_game(training=False)

    started = game.start_game()

    assert started is True
    assert game.status == "RUNNING"
    assert game.phase == "WORK"
    assert game.day == 1
    assert game.map_data
    assert all(not player.finished_phase for player in game.players.values())


def test_game_advances_through_work_trade_night_and_next_day(make_game, monkeypatch):
    game = make_game()
    game.start_game()
    for player in game.players.values():
        player.resources.update({"food": 5, "wood": 5, "iron": 1})
        player.fire_status = "HOST"
    monkeypatch.setattr(
        "service.game.models.player.random.random", lambda: 1.0)

    game.next_phase()
    assert game.phase == "TRADE"
    assert game.day == 1

    game.next_phase()
    assert game.phase == "NIGHT"

    game.next_phase()
    assert game.phase == "WORK"
    assert game.day == 2
    assert all(player.resources["food"] == 4 for player in game.players.values())


def test_all_living_players_finished_advances_phase_and_ignores_dead_players(make_game):
    game = make_game()
    game.start_game()
    game.players["player-1"].finished_phase = True
    game.players["player-2"].health = "dead"

    game.check_all_players_locked()

    assert game.phase == "TRADE"


def test_expired_timer_advances_phase(make_game):
    game = make_game()
    game.start_game()
    game.phase_end_time = 0

    transitioned = game.check_timer()

    assert transitioned is True
    assert game.phase == "TRADE"


def test_night_at_game_length_marks_game_ended(make_game):
    game = make_game()
    game.start_game()
    game.phase = "NIGHT"
    game.day = game.game_length

    game.next_phase()

    assert game.status == "ENDED"
    assert game.phase == "NIGHT"
    assert game.day == game.game_length


def test_night_health_change_waits_for_affected_player_acknowledgement(make_game, monkeypatch):
    game = make_game(training=False)
    game.start_game()
    game.phase = "NIGHT"
    game.players["player-1"].resources["food"] = 0
    game.players["player-1"].fire_status = "COLD"
    game.players["player-2"].resources["food"] = 5
    game.players["player-2"].fire_status = "HOST"
    health_checks = iter((0.0, 1.0))
    monkeypatch.setattr(
        "service.game.models.player.random.random", lambda: next(health_checks))

    result = game.next_phase()

    assert result == "NIGHT"
    assert game.phase == "NIGHT"
    assert game.day == 1
    assert game.night_transition["affected_player_ids"] == ["player-1"]

    assert game.acknowledge_night_transition(
        "player-2", game.night_transition["id"]
    ) is False
    assert game.acknowledge_night_transition(
        "player-1", game.night_transition["id"]
    ) is True
    assert game.phase == "WORK"
    assert game.day == 2


def test_night_health_animation_has_a_server_timeout_fallback(make_game, monkeypatch):
    now = [100.0]
    game = make_game(training=False)
    game._clock = lambda: now[0]
    game.start_game()
    game.phase = "NIGHT"
    game.players["player-1"].resources["food"] = 0
    game.players["player-1"].fire_status = "COLD"
    monkeypatch.setattr(
        "service.game.models.player.random.random", lambda: 0.0)

    game.next_phase()
    now[0] = game.night_transition["deadline"]

    assert game.check_timer() is True
    assert game.phase == "WORK"
    assert game.day == 2
