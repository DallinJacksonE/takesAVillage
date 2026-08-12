import type { VisualizationCommand } from "./runner.js";

export class VisualizationRegistry {
  private readonly commands = new Map<string, VisualizationCommand>();

  constructor(commands: VisualizationCommand[] = []) {
    commands.forEach((command) => this.register(command));
  }

  register(command: VisualizationCommand): void {
    if (this.commands.has(command.name)) throw new Error(`Duplicate visualization command: ${command.name}`);
    this.commands.set(command.name, command);
  }

  all(): VisualizationCommand[] { return [...this.commands.values()]; }
}
