import type { JsonValue, Phase } from "@takes-a-village/shared";

import type { DatabaseProvider, GameResultOptions } from "../db/contracts.js";
import type { Game, Player } from "../game/game.js";

function playerResources(player: Player) {
  return {
    wood: player.resources.wood,
    food: player.resources.food,
    iron: player.resources.iron,
  };
}

export function buildGameSnapshot(game: Game): JsonValue {
  return {
    game_id: game.id,
    day: game.day,
    players: Object.fromEntries([...game.players].map(([playerId, player]) => [playerId, {
      health: player.health,
      resources: playerResources(player),
      sick: player.sicknessChance,
      devs: [...player.developments],
    }])),
    developments: Object.fromEntries([...game.developments].map(([developmentId, development]) => [developmentId, {
      level: development.level,
      owner: development.owner_id,
      maintenance: development.maintenance_days,
      contested: development.is_contested ?? false,
    }])),
  };
}

export function buildWorkSnapshot(player: Player, game: Game): JsonValue {
  return {
    game_id: game.id,
    player_id: player.id,
    health: player.health,
    sickness_chance: player.sicknessChance,
    day_num: game.day,
    ...playerResources(player),
    available_work: [...player.availableWork],
    committed_action: player.committedAction,
  };
}

export function buildTradeSnapshot(player: Player, game: Game): JsonValue {
  return {
    game_id: game.id,
    player_id: player.id,
    health: player.health,
    sickness_chance: player.sicknessChance,
    day_num: game.day,
    ...playerResources(player),
    trade_history: [...player.tradeHistory],
  };
}

export function buildNightSnapshot(player: Player, game: Game): JsonValue {
  return {
    game_id: game.id,
    player_id: player.id,
    health: player.health,
    sickness_chance: player.sicknessChance,
    day_num: game.day,
    ...playerResources(player),
    fire_status: player.fireStatus,
    fire_guests: [...player.fireGuests],
  };
}

export async function persistPhaseCompletion(database: DatabaseProvider, game: Game, phase: Phase): Promise<void> {
  if (game.training) return;
  if (phase === "NIGHT") await database.storeGameSnapshot(game.id, game.day, phase, buildGameSnapshot(game));
  await Promise.all([...game.players.values()].map((player) => {
    if (phase === "WORK") return database.storeWorkSnapshot(buildWorkSnapshot(player, game));
    if (phase === "TRADE") return database.storeTradeSnapshot(buildTradeSnapshot(player, game));
    return database.storeNightSnapshot(buildNightSnapshot(player, game));
  }));
}

export function completedGameOptions(game: Game): GameResultOptions {
  return {
    trainingBatchId: game.training ? game.trainingSessionId : null,
    trainingGeneration: game.trainingGeneration,
    gameType: game.training ? "training" : game.botCount > 0 ? "human_bot" : "human",
    tradeCount: game.tradeCount,
    contestCount: game.contestCount,
    lieCount: [...game.lieCount.values()].reduce((total, count) => total + count, 0),
  };
}

export function buildCompletedGameData(game: Game): JsonValue {
  return {
    map: structuredClone(game.mapHistory),
    players: structuredClone(game.playerHistory),
    training: game.training,
    training_session_id: game.trainingSessionId,
    training_generation: game.trainingGeneration,
  };
}

export async function persistCompletedGame(database: DatabaseProvider, game: Game): Promise<void> {
  await database.storeGameResult(
    game.id,
    game.day,
    game.phase,
    buildCompletedGameData(game),
    completedGameOptions(game),
  );
}
