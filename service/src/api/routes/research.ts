import type { FastifyInstance } from "fastify";

import type { DatabaseProvider, GameRecord, JsonObject } from "../../db/contracts.js";
import type { ResearchVisualizationService } from "../../research/visualizations/service.js";

export interface ResearchRouteDependencies {
  database: DatabaseProvider;
  visualizations: ResearchVisualizationService;
  fetchBotModels: () => Promise<string[]>;
}

function gameContext(game: GameRecord): JsonObject {
  return {
    game_id: game.game_id,
    day_num: game.day_num,
    phase: game.phase,
    data: game.data,
    created_at: game.created_at.toISOString(),
    game_type: game.game_type ?? "human",
    training_batch_id: game.training_batch_id ?? null,
    training_generation: game.training_generation ?? null,
  };
}

export function registerResearchRoutes(app: FastifyInstance, dependencies: ResearchRouteDependencies): void {
  const { database, visualizations } = dependencies;

  app.get<{ Querystring: { search?: string; sort?: string } }>("/api/research/games", async (request) => {
    const search = request.query.search?.toLowerCase();
    let games = await database.getAllGames();
    if (search) games = games.filter((game) => [game.game_id, game.game_type, game.training_batch_id].some((value) => String(value ?? "").toLowerCase().includes(search)));
    if (request.query.sort === "name_asc" || request.query.sort === "name_desc") {
      const direction = request.query.sort === "name_asc" ? 1 : -1;
      games = [...games].sort((first, second) => first.game_id.localeCompare(second.game_id) * direction);
    }
    return games.map((game) => gameContext(game));
  });

  app.get<{ Params: { gameId: string } }>("/api/research/games/:gameId", async (request, reply) => {
    const game = (await database.getAllGames()).find((candidate) => candidate.game_id === request.params.gameId);
    if (!game) return reply.code(404).send({ detail: "Game not found" });
    const context = gameContext(game);
    return { ...context, visualizations: await visualizations.ensure("game", game.game_id, context) };
  });

  app.get("/api/research/genomes", async () => {
    const models = await dependencies.fetchBotModels().catch(() => []);
    return { genomes: await database.getAllGenomes(), models: models.length ? models : ["genetic"] };
  });

  app.get<{ Params: { visualizationId: string } }>("/api/research/visualizations/:visualizationId", async (request, reply) => {
    const item = await database.getResearchVisualization(request.params.visualizationId);
    if (!item?.image_bytes) return reply.code(404).send({ detail: "Visualization not found" });
    return reply.type(item.mime_type || "image/svg+xml").send(item.image_bytes);
  });
}
