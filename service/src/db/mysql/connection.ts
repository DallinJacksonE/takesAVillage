import mysql, { type Pool } from "mysql2/promise";

import type { ServiceConfig } from "@takes-a-village/shared";

import type { TransactionalSqlExecutor } from "./sql.js";

export interface ClosableSqlExecutor extends TransactionalSqlExecutor {
  end?(): Promise<void>;
}

export function createMySqlPool(config: ServiceConfig["database"]): ClosableSqlExecutor {
  return mysql.createPool({
    host: config.host,
    port: config.port,
    user: config.user,
    password: config.password,
    database: config.name,
    waitForConnections: true,
    connectionLimit: 10,
    dateStrings: false,
  }) as unknown as Pool & ClosableSqlExecutor;
}
