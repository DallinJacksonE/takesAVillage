import json

import pytest

from service.db.facade import DatabaseFacade
from service.db.factory import get_database
from service.db.memory import InMemoryDB
from service.db.mysql import MySQLDB
from service.db.mysql.training import TrainingRepository


def _provider(case):
    backend = InMemoryDB()
    if case == "memory":
        return backend, backend
    return DatabaseFacade(object(), repositories=[backend]), backend


def test_mysql_facade_routes_training_attempts_to_training_repository():
    database = DatabaseFacade(MySQLDB({}))

    method = database.get_training_games

    assert isinstance(method.__self__, TrainingRepository)


@pytest.mark.parametrize("case", ["memory", "facade"])
def test_provider_contract_users_games_and_snapshots(case):
    database, backend = _provider(case)

    assert database.create_user("user-1", True) is True
    assert database.user_exists("user-1") is True
    assert database.user_exists("missing") is False

    database.store_game_snapshot("game-1", 1, "WORK", json.dumps({"day": 1}))
    database.store_game_result(
        "game-1", 2, "NIGHT", json.dumps({"day": 2}),
        training_batch_id="batch-1", training_generation=2,
        trade_count=3, contest_count=4, lie_count=5,
    )
    database.store_player_snapshot("game-1", 1, "WORK", {"id": "user-1"})
    database.store_work_snapshot({"game_id": "game-1"})
    database.store_trade_snapshot({"game_id": "game-1"})
    database.store_night_snapshot({"game_id": "game-1"})

    assert [row["data"] for row in database.get_all_game_history()] == [
        {"day": 2}, {"day": 1},
    ]
    assert database.get_all_games()[0]["trade_count"] == 3
    assert database.get_all_games()[0]["contest_count"] == 4
    assert database.get_all_games()[0]["lie_count"] == 5
    assert backend.player_snapshots[0]["player"] == {"id": "user-1"}
    assert backend.work_snapshots == [{"game_id": "game-1"}]
    assert backend.trade_snapshots == [{"game_id": "game-1"}]
    assert backend.night_snapshots == [{"game_id": "game-1"}]


@pytest.mark.parametrize("case", ["memory", "facade"])
def test_provider_contract_genomes_training_and_visualizations(case):
    database, _backend = _provider(case)

    database.store_genome("genome-1", "G1", json.dumps({"food_weight": 1.0}))
    assert database.get_all_genomes()[0]["genome_data"] == {"food_weight": 1.0}

    database.create_training_batch("batch-1", {
        "ruleset": "default",
        "bot_model": "GOAPGenetic",
        "bot_count": 2,
        "total_generations": 1,
        "base_genome_id": "random",
        "config": {"games_per_generation": 1},
    })
    database.mark_training_batch_game_started("batch-1", "game-1", 1, attempt=1)
    database.mark_training_batch_game_running("batch-1", "game-1")
    database.mark_training_batch_game_completed(
        "batch-1", "game-1", 2,
        {"best_fitness": 10.0, "average_fitness": 8.0},
    )
    database.record_training_batch_heartbeat("batch-1", "aggregating", 1, "game-1")
    database.append_training_batch_generation_stats(
        "batch-1", {"generation": 1, "best_fitness": 10.0})
    database.complete_training_batch("batch-1", "genome-1")

    batch = database.get_training_batch("batch-1")
    games = database.get_training_games("batch-1")
    assert database.get_training_batches()[0]["batch_id"] == "batch-1"
    assert batch["status"] == "completed"
    assert batch["final_champion_genome_id"] == "genome-1"
    assert batch["generation_statistics"] == [
        {"generation": 1, "best_fitness": 10.0},
    ]
    assert games[0]["status"] == "completed"
    assert games[0]["attempt"] == 1
    assert games[0]["genome_count"] == 2

    visualization_id = database.store_research_visualization(
        "game", "game-1", "inventory", "Inventory", "image/png",
        b"png", {"player": "user-1"},
    )
    listing = database.get_research_visualizations("game", "game-1")
    stored = database.get_research_visualization(visualization_id)
    assert listing[0]["id"] == visualization_id
    assert "image_bytes" not in listing[0]
    assert stored["image_bytes"] == b"png"
    database.delete_research_visualizations("game", "game-1")
    assert database.get_research_visualizations("game", "game-1") == []


def test_get_database_returns_mysql_facade():
    database = get_database({
        "db_type": "mysql",
        "db": {"host": "db", "user": "village", "password": "pw", "database": "village"},
    })

    assert isinstance(database, DatabaseFacade)
    assert database.provider.__class__.__name__ == "MySQLDB"
    assert {repository.__class__.__name__ for repository in database.repositories} == {
        "UsersRepository", "GamesRepository", "GenomesRepository",
        "TrainingRepository", "VisualizationsRepository",
    }
    for method_name in (
        "create_user", "store_game_result", "store_genome",
        "create_training_batch", "store_research_visualization",
    ):
        assert callable(getattr(database, method_name))
