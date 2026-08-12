import { buildApp } from "./app.js";
import { loadServiceConfig } from "./config.js";
import { MemoryDatabase, MySqlDatabase } from "./db.js";

const config = await loadServiceConfig();
const database = config.database.type === "mysql"
  ? new MySqlDatabase(config.database)
  : new MemoryDatabase();
const app = await buildApp({
  databaseType: config.database.type,
  botSecret: config.bots.secret,
  botServiceUrl: config.bots.httpUrl,
  database,
  logger: true,
});

const port = Number(process.env.PORT ?? 5000);
await app.listen({ host: "0.0.0.0", port });

const shutdown = async (): Promise<void> => {
  await app.close();
  process.exit(0);
};
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
