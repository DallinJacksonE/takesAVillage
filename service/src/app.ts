import { randomUUID } from "node:crypto";

import cookie from "@fastify/cookie";
import cors from "@fastify/cors";
import websocket from "@fastify/websocket";
import Fastify, { type FastifyInstance } from "fastify";

import {
  botModelsResponseSchema,
  botJoinRequestSchema,
  cancelTrainingRequestSchema,
  joinGameRequestSchema,
  newGameRequestSchema,
  trainingRequestSchema,
  type TrainingSessionsDTO,
} from "@takes-a-village/shared";

import { RULESETS } from "./game/rules.js";
import { MemoryDatabase, type DatabaseProvider } from "./db.js";
import type { JsonObject } from "./db/contracts.js";
import { registerResearchRoutes } from "./api/routes/research.js";
import { ConnectionManager } from "./api/websocket/connection-manager.js";
import {
  cleanupDisconnectedPlayer,
  createGameEventMessenger,
  registerGameWebSocketRoute,
  sameSecret,
} from "./api/websocket/game-router.js";
import {
  registerTrainingWebSocketRoute,
  TrainingUpdateHub,
} from "./api/websocket/training-router.js";
import { GameLifecycleService } from "./game-manager/lifecycle.js";
import { GameLoop, type GameLoopScheduler } from "./game-manager/loop.js";
import { persistCompletedGame, persistPhaseCompletion } from "./game-manager/persistence.js";
import { GameRegistry } from "./game-manager/registry.js";
import { BotServiceClient, type TrainingBotClient } from "./research/training/bot-client.js";
import { TrainingService } from "./research/training/service.js";
import { startTrainingWatchdog, type WatchdogScheduler } from "./research/training/watchdog.js";
import { defaultBatchVisualizationCommands } from "./research/visualizations/batch-commands.js";
import { defaultGameVisualizationCommands } from "./research/visualizations/game-commands.js";
import { VisualizationRegistry } from "./research/visualizations/registry.js";
import { VisualizationRunner } from "./research/visualizations/runner.js";
import { ResearchVisualizationService } from "./research/visualizations/service.js";

export interface BuildAppOptions {
  databaseType: "memory" | "mysql";
  botSecret: string;
  botServiceUrl?: string;
  database?: DatabaseProvider;
  logger?: boolean;
  trainingHub?: TrainingUpdateHub;
  listTrainingSessions?: () => TrainingSessionsDTO;
  registry?: GameRegistry;
  scheduler?: GameLoopScheduler;
  trainingCompletionCallback?: (gameId: string, trainingSessionId: string) => void | Promise<void>;
  trainingBotClient?: TrainingBotClient;
  trainingIdFactory?: () => string;
  trainingRandom?: () => number;
  trainingClock?: () => Date;
  trainingWatchdogScheduler?: WatchdogScheduler;
  fetchBotModels?: () => Promise<string[]>;
}

export async function buildApp(options: BuildAppOptions): Promise<FastifyInstance> {
  const app = Fastify({ logger: options.logger ?? false });
  await app.register(cookie);
  await app.register(cors, { origin: true, credentials: true });
  await app.register(websocket);

  const database = options.database ?? new MemoryDatabase();
  await database.initialize();
  const trainingHub = options.trainingHub ?? new TrainingUpdateHub();
  const games = options.registry ?? new GameRegistry();
  let connections!: ConnectionManager;
  connections = new ConnectionManager((gameId, userId) => {
    cleanupDisconnectedPlayer(gameId, userId, {
      games,
      connections,
      botSecret: options.botSecret,
      botServiceUrl: options.botServiceUrl,
    });
  });
  const gameMessenger = createGameEventMessenger(connections);
  const lifecycle = new GameLifecycleService(games, {
    idFactory: randomUUID,
    onPhaseCompleted: (game, phase) =>
      persistPhaseCompletion(database, game, phase).catch((error: unknown) => {
        app.log.error({ error }, `Failed to persist ${phase} snapshots for ${game.id}`);
      }),
  });
  const trainingService = new TrainingService({
    database,
    createGame: (hostId, ruleset, createOptions) => lifecycle.createGame(hostId, ruleset, createOptions),
    botClient: options.trainingBotClient ?? new BotServiceClient(options.botServiceUrl ?? "http://bots:8001", options.botSecret),
    updateHub: trainingHub,
    idFactory: options.trainingIdFactory ?? randomUUID,
    random: options.trainingRandom,
    clock: options.trainingClock,
  });
  const listTrainingSessions = options.listTrainingSessions ?? (() => trainingService.list());
  const visualizations = new ResearchVisualizationService(
    database,
    new VisualizationRunner(database, new VisualizationRegistry(defaultGameVisualizationCommands())),
    new VisualizationRunner(database, new VisualizationRegistry(defaultBatchVisualizationCommands())),
  );
  const gameLoop = new GameLoop({
    registry: games,
    persistCompleted: (game) => persistCompletedGame(database, game),
    broadcastStates: (game) => gameMessenger.broadcastStates(game),
    trainingCompletionCallback: options.trainingCompletionCallback ?? ((gameId, sessionId) => trainingService.handleGameEnded(gameId, sessionId)),
    scheduler: options.scheduler,
    logger: {
      error: (message, error) => app.log.error({ error }, message),
    },
  });
  const stopGameLoop = gameLoop.start(250);
  const stopTrainingWatchdog = startTrainingWatchdog(
    trainingService,
    30_000,
    600_000,
    options.trainingWatchdogScheduler,
    (error) => app.log.error({ error }, "Training watchdog failed"),
  );

  app.get("/health", async () => ({ status: "ok" }));

  app.get("/api/verifySession", async (request, reply) => {
    const session = request.cookies.user_session;
    if (!session || !(await database.userExists(session))) return reply.code(401).send({ detail: "No valid session" });
    return { userId: session, message: "Session valid" };
  });

  app.post("/api/consent", async (_request, reply) => {
    const userId = randomUUID();
    await database.createUser(userId);
    reply.setCookie("user_session", userId, { maxAge: 86_400, secure: false, sameSite: "lax", path: "/" });
    return { message: "Consent logged", userId };
  });

  app.get("/api/activeGames", async (request, reply) => {
    const session = request.cookies.user_session;
    if (!session || !(await database.userExists(session))) return reply.code(403).send({ detail: "Invalid or expired session" });
    const publicGames: Array<{ id: string; name: string; players: string; isRejoinable: boolean }> = [];
    const rejoinable: typeof publicGames = [];
    for (const game of games.values()) {
      const item = { id: game.id, name: `Village ${game.id}`, players: `${game.players.size}/10`, isRejoinable: false };
      if (game.players.has(session) && (game.status === "WAITING" || game.status === "RUNNING")) rejoinable.push({ ...item, isRejoinable: true });
      else if (game.status === "WAITING") publicGames.push(item);
    }
    return { games: [...rejoinable, ...publicGames] };
  });

  app.get("/api/newGame", async () => ({ options: RULESETS }));

  app.post("/api/newGame", async (request, reply) => {
    const session = request.cookies.user_session;
    if (!session || !(await database.userExists(session))) return reply.code(403).send({ detail: "Invalid/No Session" });
    const parsed = newGameRequestSchema.safeParse(request.body);
    if (!parsed.success) return reply.code(422).send({ detail: parsed.error.issues });
    const gameId = lifecycle.createGame(session, parsed.data.ruleset, { botCount: parsed.data.botCount });
    if (parsed.data.botCount > 0 && options.botServiceUrl) {
      void fetch(`${options.botServiceUrl}/api/spawn_bots`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          gameId,
          botCount: parsed.data.botCount,
          botSecret: options.botSecret,
          botModel: parsed.data.botModel,
          baseGenome: null,
        }),
      }).catch((error: unknown) => app.log.error({ error }, "Bot service request failed"));
    }
    return { gameId };
  });

  app.post("/api/joinGame", async (request, reply) => {
    const parsed = joinGameRequestSchema.safeParse(request.body);
    if (!parsed.success) return reply.code(422).send({ detail: parsed.error.issues });
    if (!games.has(parsed.data.gameId)) return reply.code(404).send({ detail: "Game not found" });
    return { gameId: parsed.data.gameId };
  });

  app.post("/api/botJoinGame", async (request, reply) => {
    const parsed = botJoinRequestSchema.safeParse(request.body);
    if (!parsed.success) return reply.code(422).send({ detail: parsed.error.issues });
    if (!options.botSecret || !sameSecret(parsed.data.botSecret, options.botSecret)) return reply.code(403).send({ detail: "Invalid bot secret" });
    const game = games.get(parsed.data.gameId);
    if (!game) return reply.code(404).send({ detail: "Game not found" });
    if (game.status !== "WAITING") return reply.code(400).send({ detail: "Game already running" });
    const userId = `bot_${randomUUID().slice(0, 8)}`;
    game.addPlayer(userId);
    return { userId, gameId: parsed.data.gameId };
  });

  registerResearchRoutes(app, {
    database,
    visualizations,
    fetchBotModels: options.fetchBotModels ?? (async () => {
      if (!options.botServiceUrl) return [];
      const response = await fetch(`${options.botServiceUrl}/api/models`);
      if (!response.ok) return [];
      return botModelsResponseSchema.parse(await response.json()).models;
    }),
  });
  app.get("/api/research/training-batches", async () => {
    const persisted = await database.getTrainingBatches();
    const persistedIds = new Set(persisted.map((batch) => batch.batch_id));
    const active = trainingService.list().sessions
      .filter((session) => !persistedIds.has(session.session_id))
      .map((session) => ({ batch_id: session.session_id, status: "running", ...session }));
    return { batches: [...active, ...persisted] };
  });
  app.get<{ Params: { batchId: string } }>("/api/research/training-batches/:batchId", async (request, reply) => {
    const persisted = await database.getTrainingBatch(request.params.batchId);
    const active = trainingService.status(request.params.batchId);
    if (!persisted && !active) return reply.code(404).send({ detail: "Training batch not found" });
    const detail = {
      ...(persisted ?? { batch_id: request.params.batchId, status: "running" }),
      games: await database.getTrainingGames(request.params.batchId),
    };
    const context = JSON.parse(JSON.stringify(detail)) as JsonObject;
    return { ...detail, visualizations: await visualizations.ensure("training_batch", request.params.batchId, context) };
  });
  app.post<{ Params: { batchId: string } }>("/api/research/training-batches/:batchId/cancel", async (request, reply) => {
    const parsed = cancelTrainingRequestSchema.safeParse(request.body ?? {});
    if (!parsed.success) return reply.code(422).send({ detail: parsed.error.issues });
    const cancelled = await trainingService.cancel(request.params.batchId, parsed.data.reason);
    if (!cancelled && !(await database.getTrainingBatch(request.params.batchId))) return reply.code(404).send({ detail: "Training batch not found" });
    return { message: "Training batch cancelled", batch_id: request.params.batchId };
  });
  app.post<{ Params: { batchId: string } }>("/api/research/training-batches/:batchId/rerun", async (request, reply) => {
    if (!(await database.getTrainingBatch(request.params.batchId))) return reply.code(404).send({ detail: "Training batch not found" });
    void trainingService.rerun(request.params.batchId).catch((error: unknown) => app.log.error({ error }, "Training rerun failed"));
    return { message: "Training batch rerun initiated", source_batch_id: request.params.batchId };
  });
  app.post("/api/research/train", async (request, reply) => {
    const parsed = trainingRequestSchema.safeParse(request.body);
    if (!parsed.success) return reply.code(422).send({ detail: parsed.error.issues });
    void trainingService.start({
      ruleset: parsed.data.ruleset,
      botCount: parsed.data.botCount,
      generations: parsed.data.generations,
      baseGenomeId: parsed.data.baseGenome,
      botModel: parsed.data.botModel,
      mutationStrength: parsed.data.mutationStrength,
      mutationRate: parsed.data.mutationRate,
      randomImmigrantCount: parsed.data.randomImmigrantCount,
      gamesPerGeneration: parsed.data.gamesPerGeneration,
    }).catch((error: unknown) => app.log.error({ error }, "Training start failed"));
    return { message: "Training sequence initiated" };
  });
  app.get("/api/research/training-sessions", async () => listTrainingSessions());


  registerGameWebSocketRoute(app, {
    games,
    connections,
    database,
    botSecret: options.botSecret,
    botServiceUrl: options.botServiceUrl,
  });

  registerTrainingWebSocketRoute(app, trainingHub, listTrainingSessions);

  app.addHook("onClose", async () => {
    stopGameLoop();
    stopTrainingWatchdog();
    await database.close();
  });

  return app;
}
