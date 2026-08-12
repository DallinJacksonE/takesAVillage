import type {
  DevelopmentDTO,
  GameStateDTO,
  PlayerDTO,
} from "@takes-a-village/shared";

interface DevelopmentPlayer {
  readonly id: string;
  readonly resources: PlayerDTO["resources"];
  finishedPhase: boolean;
}

interface DevelopmentGame {
  readonly phase: GameStateDTO["phase"];
  readonly developments: Map<string, DevelopmentDTO>;
  readonly rules: {
    readonly MAINTENANCE_DAYS: number;
    readonly MAX_DEVELOPMENT_LEVEL: number;
  };
}

export function handleDevelopmentAction(
  game: DevelopmentGame,
  player: DevelopmentPlayer,
  command: unknown,
  payload: Record<string, unknown>,
): boolean {
  if (game.phase !== "WORK" || typeof payload.dev_id !== "string") return false;
  const development = game.developments.get(payload.dev_id);
  if (!development || development.owner_id !== player.id) return false;
  if (command === "MAINTAIN_DEV") {
    if (!deduct(player.resources, development.maintenance_cost)) return false;
    development.maintenance_days = game.rules.MAINTENANCE_DAYS;
    player.finishedPhase = true;
    return true;
  }
  if (command === "UPGRADE_DEV") {
    if (!development.can_upgrade || !deduct(player.resources, development.upgrade_cost)) return false;
    development.level = Math.min(development.level + 1, game.rules.MAX_DEVELOPMENT_LEVEL);
    development.maintenance_days = game.rules.MAINTENANCE_DAYS;
    development.can_upgrade = development.level < game.rules.MAX_DEVELOPMENT_LEVEL;
    development.maintenance_cost = maintenanceCost(development);
    development.upgrade_cost = upgradeCost(development);
    player.finishedPhase = true;
    return true;
  }
  return false;
}

export function degradeDevelopments(game: DevelopmentGame): void {
  for (const development of game.developments.values()) {
    development.maintenance_days -= 1;
    if (development.maintenance_days >= 0) continue;
    if (development.level > 1) {
      development.level -= 1;
      development.maintenance_days += game.rules.MAINTENANCE_DAYS;
    } else {
      development.level = 1;
      development.maintenance_days = 1;
    }
    development.can_upgrade = development.level < game.rules.MAX_DEVELOPMENT_LEVEL;
    development.maintenance_cost = maintenanceCost(development);
    development.upgrade_cost = upgradeCost(development);
  }
}

function maintenanceCost(development: DevelopmentDTO): Record<string, number> {
  if (development.type === "Farm") return { wood: development.level, iron: Math.max(development.level - 1, 0) };
  if (development.type === "Woods") return { food: development.level, iron: Math.max(development.level - 1, 0) };
  const amount = development.level * 2 + 1;
  return { food: amount, wood: amount };
}

function upgradeCost(development: DevelopmentDTO): Record<string, number> {
  if (development.type === "Farm") return { wood: development.level * 2 + 1, iron: development.level };
  if (development.type === "Woods") return { food: development.level * 2 + 1, iron: development.level };
  return { food: development.level, wood: development.level, iron: development.level * 2 + 1 };
}

function deduct(resources: PlayerDTO["resources"], costs: Record<string, number>): boolean {
  for (const [resource, amount] of Object.entries(costs)) {
    const key = resource as keyof PlayerDTO["resources"];
    if (resources[key] < amount) return false;
  }
  for (const [resource, amount] of Object.entries(costs)) {
    const key = resource as keyof PlayerDTO["resources"];
    resources[key] -= amount;
  }
  return true;
}
