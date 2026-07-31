import unittest

from service.research.visualizations.command import VisualizationCommand
from service.research.visualizations.registry import VisualizationRegistry
from service.research.visualizations.runner import VisualizationRunner


class _FakeFigure:
    def savefig(self, buffer, format="png", **_kwargs):
        buffer.write(f"fake-{format}".encode("utf-8"))


class _FakeCommand(VisualizationCommand):
    name = "fake"
    title = "Fake Visualization"
    description = "Test visualization"

    def render(self, context):
        return _FakeFigure()


class _FakeStorage:
    def __init__(self):
        self.calls = []

    def store_research_visualization(self, **kwargs):
        self.calls.append(kwargs)
        return "viz-1"


class VisualizationCommandTests(unittest.TestCase):
    def test_registry_rejects_duplicate_command_names(self):
        registry = VisualizationRegistry([_FakeCommand()])

        with self.assertRaises(ValueError):
            registry.register(_FakeCommand())

    def test_runner_stores_command_output_without_branching_per_command(self):
        storage = _FakeStorage()
        runner = VisualizationRunner(storage, VisualizationRegistry([_FakeCommand()]))

        results = runner.run_all("game", "game-1", {"game_id": "game-1"})

        self.assertEqual(results, ["viz-1"])
        self.assertEqual(storage.calls[0]["scope_type"], "game")
        self.assertEqual(storage.calls[0]["scope_id"], "game-1")
        self.assertEqual(storage.calls[0]["name"], "fake")
        self.assertEqual(storage.calls[0]["title"], "Fake Visualization")
        self.assertEqual(storage.calls[0]["mime_type"], "image/png")
        self.assertEqual(storage.calls[0]["image_bytes"], b"fake-png")


if __name__ == "__main__":
    unittest.main()
