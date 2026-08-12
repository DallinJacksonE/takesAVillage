import type { JsonObject, DatabaseProvider, VisualizationRecord } from "../../db/contracts.js";
import type { VisualizationRunner } from "./runner.js";

export class ResearchVisualizationService {
  constructor(
    private readonly storage: DatabaseProvider,
    private readonly gameRunner: VisualizationRunner,
    private readonly batchRunner: VisualizationRunner,
  ) {}

  async ensure(scopeType: "game" | "training_batch", scopeId: string, context: JsonObject): Promise<VisualizationRecord[]> {
    if (scopeType === "game") {
      const existing = await this.storage.getResearchVisualizations(scopeType, scopeId);
      if (existing.length) return existing;
    } else {
      await this.storage.deleteResearchVisualizations(scopeType, scopeId);
    }
    await (scopeType === "game" ? this.gameRunner : this.batchRunner).runAll(scopeType, scopeId, context);
    return this.storage.getResearchVisualizations(scopeType, scopeId);
  }
}
