from datetime import datetime

from service.api.routers import research_genomes


class _FakeBotModelsResponse:
    status_code = 200

    @staticmethod
    def json():
        return {"models": ["genetic", "GOAPGenetic"]}


class _FakeBotModelsClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def get(self, *_args, **_kwargs):
        return _FakeBotModelsResponse()


def test_research_game_list_and_detail_preserve_shape(api_context):
    client, database = api_context
    database.history.append({
        "game_id": "game-1",
        "day_num": 4,
        "phase": "NIGHT",
        "data": {"players": {}},
        "game_type": "human",
        "training_batch_id": None,
        "created_at": datetime.now(),
    })
    listed = client.get("/api/research/games?search=game-1&sort=name_asc")
    detail = client.get("/api/research/games/game-1")

    assert listed.status_code == 200
    assert [game["game_id"] for game in listed.json()] == ["game-1"]
    assert detail.status_code == 200
    assert detail.json()["game_id"] == "game-1"
    assert detail.json()["visualizations"] == []


def test_training_batch_routes_include_persisted_games(api_context):
    client, database = api_context
    database.create_training_batch("batch-1", {
        "ruleset": "default",
        "bot_model": "GOAPGenetic",
        "bot_count": 2,
        "total_generations": 1,
        "base_genome_id": "random",
        "config": {"games_per_generation": 1},
    })
    database.mark_training_batch_game_started("batch-1", "game-1", 1, 1)
    listed = client.get("/api/research/training-batches")
    detail = client.get("/api/research/training-batches/batch-1")

    assert listed.status_code == 200
    assert listed.json()["batches"][0]["batch_id"] == "batch-1"
    assert detail.status_code == 200
    assert detail.json()["batch_id"] == "batch-1"
    assert detail.json()["games"][0]["game_id"] == "game-1"
    assert detail.json()["visualizations"] == []


def test_genome_route_combines_database_genomes_and_bot_models(api_context, monkeypatch):
    client, database = api_context
    database.store_genome("candidate", "C1", '{"food_weight": 1.0}')
    monkeypatch.setattr(research_genomes.httpx, "AsyncClient", _FakeBotModelsClient)

    response = client.get("/api/research/genomes")

    assert response.status_code == 200
    assert response.json()["models"] == ["genetic", "GOAPGenetic"]
    assert response.json()["genomes"][0]["name"] == "candidate"


def test_visualization_route_returns_stored_bytes(api_context):
    client, database = api_context
    visualization_id = database.store_research_visualization(
        "game", "game-1", "chart", "Chart", "image/png", b"png-bytes"
    )

    response = client.get(f"/api/research/visualizations/{visualization_id}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"png-bytes"


def test_training_session_route_exposes_active_session_progress(api_context):
    client, database = api_context
    database.training_sessions["session-1"] = {
        "ruleset": "default",
        "bot_count": 2,
        "generation": 1,
        "generations_left": 2,
        "games_per_generation": 1,
        "games_completed": 0,
        "games_failed": 0,
        "generation_statistics": [],
        "bot_model": "GOAPGenetic",
    }

    response = client.get("/api/research/training-sessions")

    assert response.status_code == 200
    assert response.json()["sessions"][0]["session_id"] == "session-1"
