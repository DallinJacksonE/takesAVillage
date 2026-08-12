import type { Game } from "../game/game.js";
import type { GameRegistry } from "./registry.js";

export interface GameLoopLogger {
  error(message: string, error?: unknown): void;
}

export interface GameLoopScheduler {
  setInterval(callback: () => void | Promise<void>, intervalMs: number): unknown;
  clearInterval(handle: unknown): void;
}

export interface GameLoopOptions {
  registry: GameRegistry;
  persistCompleted(game: Game): void | Promise<void>;
  broadcastStates(game: Game): void | Promise<void>;
  trainingCompletionCallback?: (gameId: string, trainingSessionId: string) => void | Promise<void>;
  logger?: GameLoopLogger;
  scheduler?: GameLoopScheduler;
}

const silentLogger: GameLoopLogger = { error: () => undefined };
const defaultScheduler: GameLoopScheduler = {
  setInterval: (callback, intervalMs) => setInterval(callback, intervalMs),
  clearInterval: (handle) => clearInterval(handle as NodeJS.Timeout),
};

export class GameLoop {
  private readonly logger: GameLoopLogger;
  private readonly completing = new Set<string>();

  constructor(private readonly options: GameLoopOptions) {
    this.logger = options.logger ?? silentLogger;
  }

  async tickOnce(): Promise<void> {
    for (const game of this.options.registry.list()) {
      if (game.status === "RUNNING") {
        try {
          if (game.checkTimer()) await this.options.broadcastStates(game);
        } catch (error) {
          this.logger.error(`Failed to tick game ${game.id}`, error);
        }
        continue;
      }
      if (game.status !== "ENDED" || this.completing.has(game.id)) continue;
      this.completing.add(game.id);
      try {
        await game.waitForPhaseCompletions();
        await this.options.persistCompleted(game);
        if (game.training && game.trainingSessionId && this.options.trainingCompletionCallback) {
          try {
            const completion = this.options.trainingCompletionCallback(game.id, game.trainingSessionId);
            void Promise.resolve(completion).catch((error: unknown) => {
              this.logger.error(`Training completion failed for ${game.id}`, error);
            });
          } catch (error) {
            this.logger.error(`Training completion failed for ${game.id}`, error);
          }
        }
        this.options.registry.remove(game.id);
      } catch (error) {
        this.logger.error(`Failed to persist completed game ${game.id}`, error);
      } finally {
        this.completing.delete(game.id);
      }
    }
  }

  start(intervalMs = 100): () => void {
    const scheduler = this.options.scheduler ?? defaultScheduler;
    const handle = scheduler.setInterval(
      () => this.tickOnce().catch((error: unknown) => this.logger.error("Game loop tick failed", error)),
      intervalMs,
    );
    return () => scheduler.clearInterval(handle);
  }
}
