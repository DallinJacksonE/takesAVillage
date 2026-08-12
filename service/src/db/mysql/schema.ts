import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import type { SqlExecutor } from "./sql.js";

export async function loadSchemaStatements(): Promise<string[]> {
  const schemaPath = fileURLToPath(new URL("../../../db/schema/mysql.sql", import.meta.url));
  const schema = await readFile(schemaPath, "utf8");
  return schema.split(";").map((statement) => statement.trim()).filter(Boolean);
}

export async function initializeSchema(database: SqlExecutor): Promise<void> {
  for (const statement of await loadSchemaStatements()) await database.execute(statement);
}
