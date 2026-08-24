import unittest

from service.research.visualizations.command import VisualizationCommand
from service.research.visualizations.registry import VisualizationRegistry
from service.research.visualizations.runner import VisualizationRunner


class _FakeFigure:
    def __init__(self):
        self.closed = False

    def savefig(self, buffer, format="png", **_kwargs):
        buffer.write(f"fake-{format}".encode("utf-8"))

    def close(self):
        self.closed = True


class _FakeCommand(VisualizationCommand):
    name = "fake"
    title = "Fake Visualization"
    description = "Test visualization"

    def __init__(self):
        self.figure = None

    def render(self, context):
        self.figure = _FakeFigure()
        return self.figure


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
        command = _FakeCommand()
        runner = VisualizationRunner(storage, VisualizationRegistry([command]))

        results = runner.run_all("game", "game-1", {"game_id": "game-1"})

        self.assertEqual(results, ["viz-1"])
        self.assertEqual(storage.calls[0]["scope_type"], "game")
        self.assertEqual(storage.calls[0]["scope_id"], "game-1")
        self.assertEqual(storage.calls[0]["name"], "fake")
        self.assertEqual(storage.calls[0]["title"], "Fake Visualization")
        self.assertEqual(storage.calls[0]["mime_type"], "image/png")
        self.assertEqual(storage.calls[0]["image_bytes"], b"fake-png")

    def test_runner_closes_figures_after_storing_png_bytes(self):
        storage = _FakeStorage()
        command = _FakeCommand()
        runner = VisualizationRunner(storage, VisualizationRegistry([command]))

        runner.run_all("game", "game-1", {"game_id": "game-1"})

        self.assertIsNotNone(command.figure)
        self.assertTrue(command.figure.closed)


if __name__ == "__main__":
    unittest.main()
