from fastapi.testclient import TestClient

from service.main import create_app


class Database:
    def __init__(self):
        self.initialized = 0

    def initialize_database(self):
        self.initialized += 1

    def get_research_visualizations(self, *_args):
        return []


def test_database_initializes_during_lifespan_not_app_construction():
    database = Database()
    app = create_app(database=database, start_background_tasks=False)

    assert database.initialized == 0
    with TestClient(app):
        assert database.initialized == 1
