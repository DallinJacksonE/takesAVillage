import type { JsonValue } from "@takes-a-village/shared";

import type { GenomeRecord } from "../contracts.js";
import { decodeJson, rows, type SqlExecutor } from "./sql.js";

export class GenomesRepository {
  constructor(private readonly database: SqlExecutor) {}

  async storeGenome(name: string, shorthand: string, genome: JsonValue): Promise<void> {
    await this.database.execute(
      "INSERT INTO genomes (name, shorthand_name, genome_data) VALUES (?, ?, ?)",
      [name, shorthand, JSON.stringify(genome)],
    );
  }

  async getAllGenomes(): Promise<GenomeRecord[]> {
    const [result] = await this.database.execute("SELECT * FROM genomes ORDER BY created_at DESC");
    return rows(result).map((row) => ({ ...row, genome_data: decodeJson(row.genome_data) }) as GenomeRecord);
  }
}
