import { describe, expect, it } from "vitest";

import { MySqlDatabase } from "../../../src/db/mysql/provider.js";

class FakeExecutor {
  readonly calls: Array<{ sql: string; values: unknown[] }> = [];

  async execute(sql: string, values: unknown[] = []): Promise<[unknown, unknown[]]> {
    this.calls.push({ sql: sql.replace(/\s+/g, " ").trim(), values });
    if (sql.includes("SELECT 1 FROM users")) return [[{ found: 1 }], []];
    return [{ affectedRows: 1 }, []];
  }

  async end(): Promise<void> {}
}

describe("MySqlDatabase", () => {
  it("initializes the retained schema idempotently and delegates provider methods", async () => {
    const executor = new FakeExecutor();
    const database = new MySqlDatabase({
      type: "mysql",
      host: "db",
      port: 3306,
      user: "village",
      password: "password",
      name: "village",
    }, executor);

    await database.initialize();
    await database.initialize();
    expect(executor.calls.filter((call) => call.sql.startsWith("CREATE TABLE IF NOT EXISTS")).length).toBeGreaterThanOrEqual(18);
    expect(executor.calls.some((call) => call.sql.includes("training_batches"))).toBe(true);
    expect(executor.calls.some((call) => call.sql.includes("player_snapshots"))).toBe(true);

    await database.createUser("user-1", true);
    expect(await database.userExists("user-1")).toBe(true);
    expect(executor.calls.at(-2)?.values).toEqual(["user-1", true]);
    expect(executor.calls.at(-1)?.values).toEqual(["user-1"]);
  });
});
