from service.db.memory import InMemoryDB


def test_memory_provider_preserves_phase_snapshots():
    database = InMemoryDB()
    database.work_snapshots.append({"game_id": "game-1"})
    database.trade_snapshots.append({"game_id": "game-1"})
    database.night_snapshots.append({"game_id": "game-1"})
    assert database.work_snapshots == [{"game_id": "game-1"}]
    assert database.trade_snapshots == [{"game_id": "game-1"}]
    assert database.night_snapshots == [{"game_id": "game-1"}]


def test_memory_provider_preserves_completed_game_counters():
    database = InMemoryDB()

    database.store_game_result(
        "game-1", 2, "NIGHT", "{}", trade_count=3,
        contest_count=4, lie_count=5,
    )

    assert database.history[0]["trade_count"] == 3
    assert database.history[0]["contest_count"] == 4
    assert database.history[0]["lie_count"] == 5
