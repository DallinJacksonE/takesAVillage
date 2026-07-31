from service.logging import BackendLogger
from service.research.visualizations.batch_commands import (
    default_batch_visualization_commands,
)
from service.research.visualizations.game_commands import (
    default_game_visualization_commands,
)
from service.research.visualizations.registry import VisualizationRegistry
from service.research.visualizations.runner import VisualizationRunner


class VisualizationService:
    def __init__(self, storage, game_runner=None, batch_runner=None, logger=None):
        self.storage = storage
        self.game_runner = game_runner or VisualizationRunner(
            storage, VisualizationRegistry(default_game_visualization_commands())
        )
        self.batch_runner = batch_runner or VisualizationRunner(
            storage, VisualizationRegistry(default_batch_visualization_commands())
        )
        self.logger = logger or BackendLogger("visualizations")

    def ensure(self, scope_type: str, scope_id: str, context: dict):
        if scope_type == "game":
            existing = self.storage.get_research_visualizations(scope_type, scope_id)
            if existing:
                return existing
        if scope_type == "training_batch":
            self.storage.delete_research_visualizations(scope_type, scope_id)
        runner = self.game_runner if scope_type == "game" else self.batch_runner
        try:
            runner.run_all(scope_type, scope_id, context)
        except Exception as exc:
            self.logger.warning(
                f"Failed to generate {scope_type} visualizations for {scope_id}: {exc}"
            )
        return self.storage.get_research_visualizations(scope_type, scope_id)
