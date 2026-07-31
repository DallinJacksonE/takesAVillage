from service.research.visualizations.service import VisualizationService


class Storage:
    def __init__(self):
        self.items = []
        self.deleted = []

    def get_research_visualizations(self, scope_type, scope_id):
        return list(self.items)

    def delete_research_visualizations(self, scope_type, scope_id):
        self.deleted.append((scope_type, scope_id))
        self.items.clear()


class Runner:
    def __init__(self):
        self.calls = []

    def run_all(self, scope_type, scope_id, context):
        self.calls.append((scope_type, scope_id, context))


def test_completed_game_visualizations_are_cached():
    storage = Storage()
    storage.items = [{"id": "viz-1"}]
    runner = Runner()
    service = VisualizationService(storage, game_runner=runner, batch_runner=runner)

    result = service.ensure("game", "game-1", {})

    assert result == [{"id": "viz-1"}]
    assert runner.calls == []


def test_training_visualizations_are_regenerated():
    storage = Storage()
    storage.items = [{"id": "old"}]
    runner = Runner()
    service = VisualizationService(storage, game_runner=runner, batch_runner=runner)

    service.ensure("training_batch", "batch-1", {"batch_id": "batch-1"})

    assert storage.deleted == [("training_batch", "batch-1")]
    assert runner.calls[0][:2] == ("training_batch", "batch-1")
