import {
  bestTrainingGenomeResponseSchema,
  spawnBotsResponseSchema,
  trainingGenomeEntriesResponseSchema,
  type JsonValue,
  type TrainingGenomeEntry,
} from "@takes-a-village/shared";

export interface BotServiceResult {
  ok: boolean;
  errorMessage?: string;
  entries?: TrainingGenomeEntry[];
}

export interface SpawnTrainingBotsInput {
  gameId: string;
  botCount: number;
  botModel: string;
  baseGenome?: JsonValue;
  trainingAttemptIndex?: number;
}

export interface TrainingBotClient {
  spawnBots(input: SpawnTrainingBotsInput): Promise<BotServiceResult>;
  fetchGameGenomes(gameId: string): Promise<BotServiceResult>;
}

export interface BotServiceClientOptions {
  fetcher?: typeof fetch;
  sleep?: (milliseconds: number) => Promise<void>;
  retryDelayMilliseconds?: number;
  genomeFetchAttempts?: number;
}

export class BotServiceClient implements TrainingBotClient {
  private readonly fetcher: typeof fetch;
  private readonly sleep: (milliseconds: number) => Promise<void>;
  private readonly retryDelayMilliseconds: number;
  private readonly genomeFetchAttempts: number;
  private readonly baseUrl: string;

  constructor(baseUrl: string, private readonly botSecret: string, options: BotServiceClientOptions = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetcher = options.fetcher ?? fetch;
    this.sleep = options.sleep ?? ((milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds)));
    this.retryDelayMilliseconds = options.retryDelayMilliseconds ?? 100;
    this.genomeFetchAttempts = Math.max(1, options.genomeFetchAttempts ?? 3);
  }

  async spawnBots(input: SpawnTrainingBotsInput): Promise<BotServiceResult> {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/spawn_bots`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          gameId: input.gameId,
          botCount: input.botCount,
          botSecret: this.botSecret,
          botModel: input.botModel,
          ...(input.baseGenome === undefined ? {} : { baseGenome: input.baseGenome }),
          ...(input.trainingAttemptIndex === undefined ? {} : { trainingAttemptIndex: input.trainingAttemptIndex }),
        }),
      });
      if (!response.ok) return { ok: false, errorMessage: await response.text() || "Bot service rejected spawn request" };
      spawnBotsResponseSchema.parse(await response.json());
      return { ok: true };
    } catch (error) {
      return { ok: false, errorMessage: error instanceof Error ? error.message : String(error) };
    }
  }

  async fetchGameGenomes(gameId: string): Promise<BotServiceResult> {
    let lastError = "No genome entries returned";
    for (let attempt = 0; attempt < this.genomeFetchAttempts; attempt += 1) {
      try {
        const response = await this.fetcher(`${this.baseUrl}/api/genomes/${gameId}/all`, {});
        if (response.ok) return { ok: true, entries: trainingGenomeEntriesResponseSchema.parse(await response.json()).entries };
        lastError = await response.text() || lastError;
      } catch (error) {
        lastError = error instanceof Error ? error.message : String(error);
      }
      if (attempt < this.genomeFetchAttempts - 1) await this.sleep(this.retryDelayMilliseconds);
    }
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/genomes/${gameId}`, {});
      if (!response.ok) return { ok: false, errorMessage: await response.text() || lastError, entries: [] };
      const parsed = bestTrainingGenomeResponseSchema.parse(await response.json());
      return parsed.genome
        ? { ok: true, entries: [{ game_id: gameId, fitness: parsed.best_fitness ?? 0, genome: parsed.genome }] }
        : { ok: true, entries: [] };
    } catch (error) {
      return { ok: false, errorMessage: error instanceof Error ? error.message : lastError, entries: [] };
    }
  }
}
