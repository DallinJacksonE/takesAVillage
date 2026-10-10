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
            try:
                image_bytes = self._figure_to_png(figure)
                metadata = {"description": getattr(command, "description", "")}
                context_version = context.get("_visualization_context_version")
                if context_version:
                    metadata["context_version"] = context_version
                visualization_id = self.storage.store_research_visualization(
                    scope_type=scope_type,
                    scope_id=scope_id,
                    name=command.name,
                    title=command.title,
                    mime_type="image/png",
                    image_bytes=image_bytes,
                    metadata=metadata,
                )
            finally:
                self._close_figure(figure)
            visualization_ids.append(visualization_id)
        return visualization_ids

    def _figure_to_png(self, figure) -> bytes:
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png")
        buffer.seek(0)
        return buffer.read()

    def _close_figure(self, figure):
        close = getattr(figure, "close", None)
        if callable(close):
            close()
            return

        try:
            import matplotlib.pyplot as plt
            plt.close(figure)
        except Exception:
            pass
