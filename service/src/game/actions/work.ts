import {
  commitWorkPayloadSchema,
  type EmploymentActionDTO,
  type GameStateDTO,
  type PlayerDTO,
  type WorkActionDTO,
} from "@takes-a-village/shared";

interface WorkPlayer {
  readonly id: string;
  readonly actions: PlayerDTO["actions"];
  readonly resources: PlayerDTO["resources"];
  readonly timeline: PlayerDTO["timeline"];
  health: PlayerDTO["health"];
  finishedPhase: boolean;
  committedAction: PlayerDTO["committed_action"];
}

interface WorkGame {
  readonly players: Map<string, WorkPlayer>;
  readonly developments: Map<string, GameStateDTO["developments"][number]>;
  readonly phase: GameStateDTO["phase"];
}

export function handleWorkAction(
  game: WorkGame,
  player: WorkPlayer,
  command: unknown,
  payload: Record<string, unknown>,
): boolean {
  if (command !== "COMMIT_WORK" || game.phase !== "WORK" || player.health !== "healthy") return false;
  const parsed = commitWorkPayloadSchema.safeParse(payload);
  if (!parsed.success) return false;
  const job = parsed.data.job;
  const liveDevelopment = game.developments.get(job.development.id);
  if (liveDevelopment?.is_contested) return false;
  if (job.action_id) {
    const employment = player.actions.find(
      (action): action is EmploymentActionDTO => action.id === job.action_id && action.type === "EMPLOYMENT",
    );
    if (!employment || employment.status !== "ACCEPTED") return false;
    employment.status = "COMPLETED";
  }
  player.committedAction = job;
  player.finishedPhase = true;
  return true;
}

export function resolveWork(game: WorkGame): void {
  for (const worker of game.players.values()) {
    if (worker.health === "sick" || worker.health === "recovering" || worker.health === "dead") continue;
    const job = asWorkAction(worker.committedAction);
    if (!job) continue;
    const owner = game.players.get(job.development.owner_id);
    const resource = developmentOutput(job.development.type);
    if (!owner || !resource) continue;
    owner.resources[resource] += job.development.level;
    if (owner.id !== worker.id) {
      owner.timeline.push({
        type: "LABOR_EXPLOITED",
        data: { worker: worker.id, yield: job.development.level, type: resource },
      });
    }
  }
  for (const player of game.players.values()) {
    player.committedAction = null;
    for (let index = player.actions.length - 1; index >= 0; index -= 1) {
      if (player.actions[index]?.type === "EMPLOYMENT") player.actions.splice(index, 1);
    }
  }
}

function asWorkAction(value: PlayerDTO["committed_action"]): WorkActionDTO | null {
  if (!value || !("development" in value)) return null;
  return value;
}

function developmentOutput(type: GameStateDTO["developments"][number]["type"]): keyof PlayerDTO["resources"] {
  if (type === "Farm") return "food";
  if (type === "Woods") return "wood";
  return "iron";
}
