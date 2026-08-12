#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import { createServer } from "node:net";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

import { rootConfigSchema } from "@takes-a-village/shared";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const profileName = process.argv[2];
const printOnly = process.argv.includes("--print");

if (profileName !== "development" && profileName !== "production") {
  console.error("Usage: node docker/compose.mjs <development|production> [--print]");
  process.exit(2);
}

const rawConfig = JSON.parse(await readFile(resolve(repositoryRoot, "config.json"), "utf8"));
const config = rootConfigSchema.parse(rawConfig);
const profile = config[profileName];
const portEnvironment = {
  HOST_DATABASE_PORT: String(profile.database),
  HOST_SERVICE_PORT: String(profile.service),
  HOST_BOTS_PORT: String(profile.bots),
  HOST_FRONTEND_PORT: String(profile.frontend),
};

async function assertPortAvailable(name, port) {
  await new Promise((resolveCheck, reject) => {
    const server = createServer();
    server.once("error", () => reject(new Error(`${profileName} ${name} host port ${port} is already in use`)));
    server.listen(port, "127.0.0.1", () => server.close(resolveCheck));
  });
}

if (printOnly) {
  process.stdout.write(`${JSON.stringify(portEnvironment, null, 2)}\n`);
  process.exit(0);
}

const forwarded = process.argv.slice(3).filter((argument) => argument !== "--print");
const composeArguments = forwarded.length ? forwarded : ["up", "--build"];
if (composeArguments[0] === "up") {
  for (const [name, port] of Object.entries(profile)) await assertPortAvailable(name, port);
}
const child = spawn("docker", ["compose", "--project-name", `takes-a-village-${profileName}`, ...composeArguments], {
  cwd: repositoryRoot,
  env: { ...process.env, ...portEnvironment },
  stdio: "inherit",
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
