import json

import mysql.connector
import pytest

from service.db.mysql.games import GamesRepository
from service.db.mysql.genomes import GenomesRepository
from service.db.mysql.training import TrainingRepository
from service.db.mysql.users import UsersRepository
from service.db.mysql.visualizations import VisualizationsRepository


class FakeCursor:
    def __init__(self, error=None, row=None):
        self.error = error
        self.row = row
        self.closed = False
        self.executions = []
        self.lastrowid = 1

    def execute(self, query, params=None):
        self.executions.append((query, params))
        if self.error:
            raise self.error

    def fetchone(self):
        return self.row

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, error=None, row=None):
        self.cursor_instance = FakeCursor(error, row)
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self, **_kwargs):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class ConnectionProvider:
    def __init__(self, connection):
        self.connection = connection

    def get_connection(self):
        return self.connection


@pytest.mark.parametrize(
    ("repository_type", "operation"),
    [
        (UsersRepository, lambda repository: repository.create_user("user-1", True)),
        (GamesRepository, lambda repository: repository.store_game_result(
            "game-1", 1, "NIGHT", "{}")),
        (GenomesRepository, lambda repository: repository.store_genome(
            "genome-1", "G1", "{}")),
        (TrainingRepository, lambda repository: repository.create_training_batch(
            "batch-1", {"config": {}})),
        (VisualizationsRepository, lambda repository: repository.delete_research_visualizations(
            "game", "game-1")),
    ],
)
def test_mysql_repository_write_commits_and_closes(repository_type, operation):
    connection = FakeConnection()
    repository = repository_type(ConnectionProvider(connection))

    operation(repository)

    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.cursor_instance.closed is True
    assert connection.closed is True


@pytest.mark.parametrize(
    ("repository_type", "operation"),
    [
        (UsersRepository, lambda repository: repository.create_user("user-1", True)),
        (GamesRepository, lambda repository: repository.store_game_result(
            "game-1", 1, "NIGHT", "{}")),
        (GenomesRepository, lambda repository: repository.store_genome(
            "genome-1", "G1", "{}")),
        (TrainingRepository, lambda repository: repository.create_training_batch(
            "batch-1", {"config": {}})),
        (VisualizationsRepository, lambda repository: repository.delete_research_visualizations(
            "game", "game-1")),
    ],
)
def test_mysql_repository_write_rolls_back_and_closes_on_error(
        repository_type, operation):
    connection = FakeConnection(mysql.connector.Error("write failed"))
    repository = repository_type(ConnectionProvider(connection))

    try:
        operation(repository)
    except mysql.connector.Error:
        pass

    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.cursor_instance.closed is True
    assert connection.closed is True


def test_training_game_updates_lock_and_preserve_existing_attempts():
    connection = FakeConnection(row={"games": '[{"game_id": "game-1"}]'})
    repository = TrainingRepository(ConnectionProvider(connection))

    result = repository.mark_training_batch_game_started(
        "batch-1", "game-2", 1, attempt=2)

    assert result is True
    select, update = connection.cursor_instance.executions
    assert "FOR UPDATE" in select[0]
    games = json.loads(update[1][0])
    assert [game["game_id"] for game in games] == ["game-1", "game-2"]
    assert connection.commits == 1
    assert connection.rollbacks == 0
