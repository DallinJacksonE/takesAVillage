export interface SqlExecutor {
  execute(sql: string, values?: unknown[]): Promise<[unknown, unknown[]]>;
}

export interface SqlConnection extends SqlExecutor {
  beginTransaction(): Promise<void>;
  commit(): Promise<void>;
  rollback(): Promise<void>;
  release(): void;
}

export interface TransactionalSqlExecutor extends SqlExecutor {
  getConnection?(): Promise<SqlConnection>;
}

export interface SqlResult {
  affectedRows?: number;
  insertId?: number | bigint;
}

export function rows(result: unknown): Record<string, unknown>[] {
  return Array.isArray(result) ? result as Record<string, unknown>[] : [];
}

export function decodeJson(value: unknown): unknown {
  if (typeof value === "string") return JSON.parse(value) as unknown;
  if (Buffer.isBuffer(value)) return JSON.parse(value.toString("utf8")) as unknown;
  return value;
}
