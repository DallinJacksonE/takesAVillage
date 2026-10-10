from abc import ABC, abstractmethod


class VisualizationCommand(ABC):
    """Command interface for generating one research visualization."""

    name: str
    title: str
    description: str = ""

    @abstractmethod
    def render(self, context):
        """Return a matplotlib-like Figure with a savefig() method."""
        raise NotImplementedError
