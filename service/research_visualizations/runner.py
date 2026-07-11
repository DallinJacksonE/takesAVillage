import io


class VisualizationRunner:
    """Runs registered visualization commands and stores their rendered images."""

    def __init__(self, storage, registry):
        self.storage = storage
        self.registry = registry

    def run_all(self, scope_type: str, scope_id: str, context: dict) -> list:
        visualization_ids = []
        for command in self.registry.all():
            figure = command.render(context)
            image_bytes = self._figure_to_png(figure)
            visualization_id = self.storage.store_research_visualization(
                scope_type=scope_type,
                scope_id=scope_id,
                name=command.name,
                title=command.title,
                mime_type="image/png",
                image_bytes=image_bytes,
                metadata={"description": getattr(command, "description", "")},
            )
            visualization_ids.append(visualization_id)
        return visualization_ids

    def _figure_to_png(self, figure) -> bytes:
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png")
        buffer.seek(0)
        return buffer.read()
