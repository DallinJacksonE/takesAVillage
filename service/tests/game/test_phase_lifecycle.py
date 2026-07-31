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
