import { spawn, type ChildProcess } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export interface RunningService {
  baseUrl: string;
  stop(): Promise<void>;
}

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");

async function availablePort(): Promise<number> {
  return await new Promise((resolvePort, reject) => {
    const server = createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (!address || typeof address === "string") {
        server.close();
        reject(new Error("Unable to allocate an ephemeral port"));
        return;
      }
      server.close((error) => error ? reject(error) : resolvePort(address.port));
    });
  });
}

async function waitUntilReady(baseUrl: string, process: ChildProcess, output: () => string): Promise<void> {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    if (process.exitCode !== null) {
      throw new Error(`Service exited with ${process.exitCode}:\n${output()}`);
    }
    try {
      const response = await fetch(`${baseUrl}/api/newGame`);
      if (response.ok) return;
    } catch {
      // The socket is expected to refuse connections while the service starts.
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 50));
  }
  throw new Error(`Timed out waiting for service:\n${output()}`);
}

export async function startService(): Promise<RunningService> {
  const port = await availablePort();
  const workingDirectory = await mkdtemp(join(tmpdir(), "takes-a-village-characterization-"));
  const chunks: string[] = [];
  const serviceCommand = globalThis.process.env.SERVICE_COMMAND;
  const process = spawn(
    serviceCommand ? "/bin/sh" : globalThis.process.execPath,
    serviceCommand
      ? ["-c", serviceCommand]
      : [resolve(repositoryRoot, "service/dist/main.js")],
    {
      cwd: serviceCommand ? repositoryRoot : workingDirectory,
      env: {
        ...globalThis.process.env,
        SERVICE_CONFIG_PATH: resolve(repositoryRoot, "service/config.test.json"),
        PORT: String(port),
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  process.stdout?.on("data", (chunk: Buffer) => chunks.push(chunk.toString()));
  process.stderr?.on("data", (chunk: Buffer) => chunks.push(chunk.toString()));

  const baseUrl = `http://127.0.0.1:${port}`;
  try {
    await waitUntilReady(baseUrl, process, () => chunks.join(""));
  } catch (error) {
    process.kill("SIGTERM");
    await rm(workingDirectory, { recursive: true, force: true });
    throw error;
  }

  return {
    baseUrl,
    async stop() {
      if (process.exitCode === null) {
        process.kill("SIGTERM");
        await Promise.race([
          new Promise<void>((resolveExit) => process.once("exit", () => resolveExit())),
          new Promise<void>((resolveTimeout) => setTimeout(resolveTimeout, 2_000)),
        ]);
        if (process.exitCode === null) process.kill("SIGKILL");
      }
      await rm(workingDirectory, { recursive: true, force: true });
    },
  };
}
