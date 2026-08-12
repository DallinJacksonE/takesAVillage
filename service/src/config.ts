import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

import { serviceConfigSchema, type ServiceConfig } from "@takes-a-village/shared";

export async function loadServiceConfig(path = process.env.SERVICE_CONFIG_PATH ?? resolve("service/config.json")): Promise<ServiceConfig> {
  let parsed: unknown;
  try {
    parsed = JSON.parse(await readFile(path, "utf8"));
  } catch (error) {
    const reason = error instanceof Error ? error.message.replace(path, "<config>") : "unknown error";
    throw new Error(`Unable to load service configuration: ${reason}`);
  }
  return Object.freeze(serviceConfigSchema.parse(parsed));
}
