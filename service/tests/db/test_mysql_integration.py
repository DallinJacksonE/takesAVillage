import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from service.db.factory import get_database


pytestmark = pytest.mark.skipif(
    not os.environ.get("MYSQL_TEST_HOST"),
    reason="requires a disposable MySQL instance",
)


def test_mysql_schema_and_representative_crud():
    database = get_database({
        "db_type": "mysql",
        "db": {
            "host": os.environ["MYSQL_TEST_HOST"],
            "port": int(os.environ.get("MYSQL_TEST_PORT", "3306")),
            "user": os.environ.get("MYSQL_TEST_USER", "village"),
            "password": os.environ.get("MYSQL_TEST_PASSWORD", "village_db"),
            "database": os.environ.get("MYSQL_TEST_DATABASE", "village_db"),
        },
    })
    suffix = uuid.uuid4().hex[:8]
    user_id = f"user-{suffix}"
    game_id = f"game-{suffix}"
    batch_id = f"batch-{suffix}"
    genome_name = f"genome-{suffix}"

    database.initialize_database()

    assert database.create_user(user_id, True) is True
    assert database.user_exists(user_id) is True

    database.store_game_snapshot(game_id, 1, "WORK", json.dumps({"day": 1}))
    database.store_game_result(
        game_id, 2, "NIGHT", json.dumps({"day": 2}),
        training_batch_id=batch_id, training_generation=1,
        trade_count=2, contest_count=3, lie_count=4,
    )
    games = database.get_all_games()
    history = database.get_all_game_history()
    assert any(row["game_id"] == game_id and row["lie_count"] == 4 for row in games)
    assert any(row["game_id"] == game_id and row["data"] == {"day": 1} for row in history)

    database.store_genome(genome_name, f"G{suffix[:3]}", json.dumps({"food_weight": 1.0}))
    assert any(
        row["name"] == genome_name and row["genome_data"] == {"food_weight": 1.0}
        for row in database.get_all_genomes()
    )

    database.create_training_batch(batch_id, {
        "ruleset": "default",
        "bot_model": "GOAPGenetic",
        "bot_count": 2,
        "total_generations": 1,
        "base_genome_id": "random",
        "config": {"games_per_generation": 1},
    })
    concurrent_game_ids = [f"{game_id}-a", f"{game_id}-b"]
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(
            lambda concurrent_game_id: database.mark_training_batch_game_started(
                batch_id, concurrent_game_id, 1),
            concurrent_game_ids,
        ))
    assert {
        game["game_id"] for game in database.get_training_games(batch_id)
    } == set(concurrent_game_ids)
    database.record_training_batch_heartbeat(batch_id, "running", 1, game_id)
    database.append_training_batch_generation_stats(
        batch_id, {"generation": 1, "best_fitness": 10.0})
    database.complete_training_batch(batch_id, genome_name)
    batch = database.get_training_batch(batch_id)
    assert batch["status"] == "completed"
    assert batch["final_champion_genome_id"] == genome_name
    assert batch["generation_statistics"] == [
        {"generation": 1, "best_fitness": 10.0},
    ]

    visualization_id = database.store_research_visualization(
        "game", game_id, "inventory", "Inventory", "image/png",
        b"png-data", {"source": "integration-test"},
    )
    listing = database.get_research_visualizations("game", game_id)
    visualization = database.get_research_visualization(visualization_id)
    assert listing[0]["id"] == visualization_id
    assert visualization["image_bytes"] == b"png-data"
    assert visualization["metadata"] == {"source": "integration-test"}
