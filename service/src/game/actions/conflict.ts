import {
  contestDevPayloadSchema,
  type CommittedContestActionDTO,
  type DevelopmentDTO,
  type PlayerDTO,
} from "@takes-a-village/shared";

export interface ContestDevelopment extends DevelopmentDTO {
  pendingContestDay?: number;
}

interface ContestPlayer {
  readonly id: string;
  readonly developments: string[];
  readonly timeline: PlayerDTO["timeline"];
  health: PlayerDTO["health"];
  committedAction: PlayerDTO["committed_action"];
  finishedPhase: boolean;
}

interface ContestGame {
  readonly players: Map<string, ContestPlayer>;
  readonly developments: Map<string, ContestDevelopment>;
  readonly day: number;
  readonly phase: "WORK" | "TRADE" | "NIGHT";
}

export function handleContestAction(
  game: ContestGame,
  player: ContestPlayer,
  command: unknown,
  payload: Record<string, unknown>,
): boolean {
  if (command !== "CONTEST_DEV" || game.phase !== "WORK" || player.health === "sick" || player.health === "recovering") {
    return false;
  }
  const parsed = contestDevPayloadSchema.safeParse(payload);
  if (!parsed.success) return false;
  const development = game.developments.get(parsed.data.dev_id);
  if (!development) return false;

  if (parsed.data.side !== "INITIATOR") {
    if (!development.is_contested || (parsed.data.side !== "CONTESTER" && parsed.data.side !== "OWNER")) return false;
    const supporters = parsed.data.side === "CONTESTER"
      ? development.contester_supporters
      : development.owner_supporters;
    if (!supporters?.includes(player.id)) supporters?.push(player.id);
    player.committedAction = {
      type: "CONTEST_ACTION",
      dev_id: development.id,
      side: parsed.data.side,
    };
    player.timeline.push({
      type: "ACTION_COMPLETED",
      data: { action: "CONTEST", dev_id: development.id, side: parsed.data.side },
    });
    player.finishedPhase = true;
    return true;
  }

  if (development.is_contested
    || development.pending_contest
    || development.owner_id === player.id) return false;

  development.pending_contest = true;
  development.pendingContestDay = game.day + 1;
  development.contest_initiator_id = player.id;
  player.timeline.push({
    type: "ACTION_COMPLETED",
    data: { action: "CONTEST_SCHEDULED", dev_id: development.id },
  });
  player.finishedPhase = true;
  return true;
}

export function activatePendingContests(game: ContestGame): void {
  for (const development of game.developments.values()) {
    if (!development.pending_contest || development.pendingContestDay !== game.day) continue;
    development.is_contested = true;
    development.contester_supporters = [];
    development.pending_contest = false;
    const owner = game.players.get(development.owner_id);
    if (owner) {
      owner.timeline.push({
        type: "CONTEST_STARTED",
        data: { dev_id: development.id, attacker: development.contest_initiator_id ?? null },
      });
    }
  }
}

export function resolveContests(game: ContestGame): void {
  for (const development of game.developments.values()) {
    if (!development.is_contested) continue;
    development.contester_supporters = [];
    development.owner_supporters = [];
    for (const player of game.players.values()) {
      const action = asContestAction(player.committedAction);
      if (!action || action.dev_id !== development.id) continue;
      if (action.side === "CONTESTER") development.contester_supporters.push(player.id);
      else development.owner_supporters.push(player.id);
    }

    const attackerId = development.contest_initiator_id;
    const attackerPresent = typeof attackerId === "string" && development.contester_supporters.includes(attackerId);
    const ownerPresent = development.owner_supporters.includes(development.owner_id);
    if (!attackerPresent) endContest(development);
    else if (!ownerPresent || development.contester_supporters.length > development.owner_supporters.length) {
      const oldOwner = game.players.get(development.owner_id);
      const newOwner = game.players.get(attackerId);
      if (oldOwner) removeValue(oldOwner.developments, development.id);
      if (newOwner && !newOwner.developments.includes(development.id)) newOwner.developments.push(development.id);
      development.owner_id = attackerId;
      endContest(development);
    }
    else if (development.owner_supporters.length > development.contester_supporters.length) endContest(development);

    development.contester_supporters = [];
    development.owner_supporters = [];
  }
}

function asContestAction(action: PlayerDTO["committed_action"]): CommittedContestActionDTO | null {
  if (!action || !("type" in action) || action.type !== "CONTEST_ACTION") return null;
  return action;
}

function endContest(development: ContestDevelopment): void {
  development.is_contested = false;
  development.contest_initiator_id = null;
}

function removeValue(values: string[], value: string): void {
  const index = values.indexOf(value);
  if (index >= 0) values.splice(index, 1);
}
