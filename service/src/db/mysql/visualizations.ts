import type { StoreVisualizationInput, VisualizationRecord } from "../contracts.js";
import { decodeJson, rows, type SqlExecutor, type SqlResult } from "./sql.js";

function decodeVisualization(row: Record<string, unknown>, includeUrl = false): VisualizationRecord {
  const id = String(row.id);
  return {
    ...row,
    id,
    metadata: (decodeJson(row.metadata) ?? {}) as VisualizationRecord["metadata"],
    ...(includeUrl ? { url: `/api/research/visualizations/${id}` } : {}),
  } as VisualizationRecord;
}

export class VisualizationsRepository {
  constructor(private readonly database: SqlExecutor) {}

  async deleteResearchVisualizations(scopeType: string, scopeId: string): Promise<void> {
    await this.database.execute(
      "DELETE FROM research_visualizations WHERE scope_type = ? AND scope_id = ?",
      [scopeType, scopeId],
    );
  }

  async storeResearchVisualization(input: StoreVisualizationInput): Promise<string> {
    const [result] = await this.database.execute(
      `INSERT INTO research_visualizations
       (scope_type, scope_id, name, title, mime_type, image_bytes, metadata)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [input.scopeType, input.scopeId, input.name, input.title, input.mimeType, input.imageBytes, JSON.stringify(input.metadata ?? {})],
    );
    return String((result as SqlResult).insertId);
  }

  async getResearchVisualizations(scopeType: string, scopeId: string): Promise<VisualizationRecord[]> {
    const [result] = await this.database.execute(
      `SELECT id, scope_type, scope_id, name, title, mime_type, metadata, created_at
       FROM research_visualizations WHERE scope_type = ? AND scope_id = ? ORDER BY created_at ASC`,
      [scopeType, scopeId],
    );
    return rows(result).map((row) => decodeVisualization(row, true));
  }

  async getResearchVisualization(visualizationId: string): Promise<VisualizationRecord | null> {
    const [result] = await this.database.execute(
      "SELECT * FROM research_visualizations WHERE id = ? LIMIT 1",
      [visualizationId],
    );
    const row = rows(result)[0];
    return row ? decodeVisualization(row) : null;
  }
}
