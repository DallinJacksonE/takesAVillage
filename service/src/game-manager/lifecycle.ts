import { randomUUID } from "node:crypto";

import { Game, type PhaseCompletedCallback } from "../game/game.js";
import { GameRegistry } from "./registry.js";

export interface CreateGameOptions {
  botCount?: number;
  training?: boolean;
  trainingSessionId?: string | null;
  trainingGeneration?: number | null;
}

export interface GameLifecycleOptions {
  idFactory?: () => string;
  clock?: () => number;
  onPhaseCompleted?: PhaseCompletedCallback;
}

export class GameLifecycleService {
  private readonly idFactory: () => string;
  private readonly clock: () => number;
  private readonly onPhaseCompleted?: PhaseCompletedCallback;

  constructor(private readonly registry: GameRegistry, options: GameLifecycleOptions = {}) {
    this.idFactory = options.idFactory ?? randomUUID;
    this.clock = options.clock ?? (() => Date.now() / 1000);
    this.onPhaseCompleted = options.onPhaseCompleted;
  }

  createGame(hostId: string, rulesetName: string, options: CreateGameOptions = {}): string {
    const gameId = `g_${this.idFactory().slice(0, 4)}`;
    this.registry.create(new Game(
      gameId,
      hostId,
      rulesetName,
      options.botCount ?? 0,
      options.training ?? false,
      this.clock,
      {
        trainingSessionId: options.trainingSessionId ?? null,
        trainingGeneration: options.trainingGeneration ?? null,
        onPhaseCompleted: this.onPhaseCompleted,
      },
    ));
    return gameId;
  }
}
