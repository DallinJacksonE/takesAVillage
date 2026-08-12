import type { JsonObject } from "../../db/contracts.js";
import type { DatabaseProvider } from "../../db/contracts.js";
import type { VisualizationRegistry } from "./registry.js";

export interface VisualizationCommand {
  name: string;
  title: string;
  description: string;
  render(context: JsonObject): string;
}

export class VisualizationRunner {
  constructor(private readonly storage: DatabaseProvider, private readonly registry: VisualizationRegistry) {}

  async runAll(scopeType: "game" | "training_batch", scopeId: string, context: JsonObject): Promise<string[]> {
    const ids: string[] = [];
    for (const command of this.registry.all()) {
      const svg = command.render(context);
      if (!svg.startsWith("<svg") || !svg.includes("</svg>")) throw new Error(`Visualization command ${command.name} returned invalid SVG`);
      ids.push(await this.storage.storeResearchVisualization({
        scopeType,
        scopeId,
        name: command.name,
        title: command.title,
        mimeType: "image/svg+xml",
        imageBytes: Buffer.from(svg, "utf8"),
        metadata: { description: command.description },
      }));
    }
    return ids;
  }
}
