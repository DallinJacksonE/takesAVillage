class VisualizationRegistry:
    """Registry that lets new visualization commands be added without branching."""

    def __init__(self, commands=None):
        self._commands = {}
        for command in commands or []:
            self.register(command)

    def register(self, command):
        if command.name in self._commands:
            raise ValueError(f"Duplicate visualization command: {command.name}")
        self._commands[command.name] = command

    def all(self):
        return list(self._commands.values())
