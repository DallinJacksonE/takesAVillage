import { randomUUID } from "node:crypto";
import type { PlayerDTO } from "@takes-a-village/shared";

interface NightPlayer {
  readonly resources: PlayerDTO["resources"];
  readonly fireGuests: string[];
  readonly availableWork: PlayerDTO["available_work"];
  readonly timeline: PlayerDTO["timeline"];
  health: PlayerDTO["health"];
  sicknessChance: number;
  fireStatus: PlayerDTO["fire_status"];
}

interface NightGame {
  readonly players: Map<string, NightPlayer>;
  readonly rules: {
    readonly DEFAULT_SICKNESS: number;
    readonly HUNGER_SICKNESS_INCREASE: number;
    readonly COLD_SICKNESS_INCREASE: number;
    readonly RECOVERY_RATE: number;
  };
}

export function resolveNightPlayers(game: NightGame): void {
  for (const player of game.players.values()) {
    const ate = player.resources.food > 0;
    if (ate) player.resources.food -= 1;
    const warm = player.fireStatus === "HOST" || player.fireStatus === "GUEST";
    updateHealth(player, ate, warm, game.rules);
    player.timeline.push({
      id: randomUUID(),
      timestamp: Date.now() / 1000,
      type: "END_OF_DAY_STATE",
      data: {
        health: player.health,
        resources: { ...player.resources },
        sickness_chance: player.sicknessChance,
      },
    });
    player.fireStatus = "COLD";
    player.fireGuests.splice(0);
    player.availableWork.splice(0);
  }
}

function updateHealth(
  player: NightPlayer,
  ate: boolean,
  warm: boolean,
  rules: NightGame["rules"],
): void {
  if (!Number.isFinite(player.sicknessChance) || player.sicknessChance === 0) {
    player.sicknessChance = rules.DEFAULT_SICKNESS;
  }
  if (!ate) player.sicknessChance += rules.HUNGER_SICKNESS_INCREASE;
  if (!warm) player.sicknessChance += rules.COLD_SICKNESS_INCREASE;
  if (ate && warm) {
    player.sicknessChance = Math.max(rules.DEFAULT_SICKNESS, player.sicknessChance - rules.RECOVERY_RATE);
  }
  if (player.health === "dead") return;
  if (ate && warm) {
    if (player.health === "sick") {
      player.health = "recovering";
      return;
    }
    if (player.health === "recovering") {
      player.health = "healthy";
      player.sicknessChance = rules.DEFAULT_SICKNESS;
      return;
    }
  }
  if (Math.random() < player.sicknessChance) {
    player.health = player.health === "sick" ? "dead" : "sick";
  }
}
