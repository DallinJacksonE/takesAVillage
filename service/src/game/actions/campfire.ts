import {
  campfireActionSchema,
  type CampfireActionDTO,
  type FireHistoryDTO,
  type PlayerDTO,
} from "@takes-a-village/shared";
import { randomUUID } from "node:crypto";

interface CampfirePlayer {
  readonly id: string;
  readonly actions: PlayerDTO["actions"];
  readonly fireGuests: string[];
  readonly fireHistory: FireHistoryDTO[];
  fireStatus: PlayerDTO["fire_status"];
}

interface CampfireGame {
  readonly players: Map<string, CampfirePlayer>;
  readonly rules: { readonly MAX_FIRE_SEATS: number };
}

export function handleCampfireAction(
  game: CampfireGame,
  player: CampfirePlayer,
  command: unknown,
  payload: Record<string, unknown>,
): boolean {
  if (command === "CAMPFIRE") return draftCampfire(game, player, payload);
  if (command === "ACCEPT") return acceptCampfire(game, player, payload.action_id);
  return false;
}

export function cleanupCampfireActions(game: CampfireGame): void {
  for (const player of game.players.values()) {
    for (let index = player.actions.length - 1; index >= 0; index -= 1) {
      if (player.actions[index]?.type === "CAMPFIRE") player.actions.splice(index, 1);
    }
  }
}

function draftCampfire(
  game: CampfireGame,
  initiator: CampfirePlayer,
  payload: Record<string, unknown>,
): boolean {
  if (typeof payload.target_id !== "string") return false;
  const target = game.players.get(payload.target_id);
  const isRequest = payload.is_request === true;
  if (!target || (!isRequest && initiator.fireStatus !== "HOST")) return false;
  const parsed = campfireActionSchema.safeParse({
    id: randomUUID(),
    initiator_id: initiator.id,
    target_id: target.id,
    type: "CAMPFIRE",
    status: "PENDING",
    waiting_on_id: target.id,
    is_request: isRequest,
  });
  if (!parsed.success) return false;
  initiator.actions.push(parsed.data);
  target.actions.push(parsed.data);
  return true;
}

function acceptCampfire(game: CampfireGame, actor: CampfirePlayer, actionId: unknown): boolean {
  const contract = findCampfire(game, actionId);
  if (!contract || contract.status !== "PENDING" || contract.waiting_on_id !== actor.id) return false;
  const hostId = contract.is_request ? contract.target_id : contract.initiator_id;
  const guestId = contract.is_request ? contract.initiator_id : contract.target_id;
  const host = hostId ? game.players.get(hostId) : undefined;
  const guest = guestId ? game.players.get(guestId) : undefined;
  if (!host || !guest
    || host.fireStatus !== "HOST"
    || guest.fireStatus === "GUEST"
    || host.fireGuests.length >= game.rules.MAX_FIRE_SEATS) return false;

  host.fireGuests.push(guest.id);
  guest.fireStatus = "GUEST";
  const guests = [...host.fireGuests];
  host.fireHistory.push({ fire_id: contract.id, host_id: host.id, role: "host", guests });
  guest.fireHistory.push({ fire_id: contract.id, host_id: host.id, role: "guest", guests: [...guests] });
  contract.status = "ACCEPTED";
  contract.waiting_on_id = null;
  return true;
}

function findCampfire(game: CampfireGame, actionId: unknown): CampfireActionDTO | undefined {
  if (typeof actionId !== "string") return undefined;
  for (const player of game.players.values()) {
    const action = player.actions.find((candidate) => candidate.id === actionId);
    if (action?.type === "CAMPFIRE") return action as CampfireActionDTO;
  }
  return undefined;
}
