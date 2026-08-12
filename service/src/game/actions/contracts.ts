import { randomUUID } from "node:crypto";

import {
  employmentActionSchema,
  tradeActionSchema,
  type DevelopmentDTO,
  type EmploymentActionDTO,
  type PartialResourceBundle,
  type TradeActionDTO,
  type TradeHistoryDTO,
  type WorkActionDTO,
} from "@takes-a-village/shared";

interface TradePlayer {
  readonly id: string;
  readonly actions: Array<{ id: string; type: string; status: string }>;
  readonly resources: Record<string, number>;
  readonly tradeHistory: TradeHistoryDTO[];
}

interface TradeGame {
  readonly players: Map<string, TradePlayer>;
}

interface EmploymentPlayer extends TradePlayer {
  readonly developments: string[];
  readonly availableWork: WorkActionDTO[];
}

interface EmploymentGame {
  readonly players: Map<string, EmploymentPlayer>;
  readonly developments: Map<string, DevelopmentDTO>;
}

export function handleEmploymentAction(
  game: EmploymentGame,
  player: EmploymentPlayer,
  command: unknown,
  payload: Record<string, unknown>,
): boolean {
  if (command === "EMPLOYMENT") return draftEmployment(game, player, payload);
  if (command === "ACCEPT") return acceptEmployment(game, player, payload.action_id);
  return false;
}

function draftEmployment(
  game: EmploymentGame,
  initiator: EmploymentPlayer,
  payload: Record<string, unknown>,
): boolean {
  if (typeof payload.target_id !== "string" || typeof payload.dev_id !== "string") return false;
  const target = game.players.get(payload.target_id);
  const development = game.developments.get(payload.dev_id);
  const isApplication = payload.is_application === true;
  const employerId = isApplication ? target?.id : initiator.id;
  if (!target || !development || development.owner_id !== employerId) return false;
  const parsed = employmentActionSchema.safeParse({
    id: randomUUID(),
    initiator_id: initiator.id,
    target_id: target.id,
    type: "EMPLOYMENT",
    status: "PENDING",
    waiting_on_id: target.id,
    dev_id: development.id,
    wage: payload.wage,
    wage_type: payload.wage_type,
    is_application: isApplication,
  });
  if (!parsed.success) return false;
  initiator.actions.push(parsed.data);
  target.actions.push(parsed.data);
  return true;
}

function acceptEmployment(game: EmploymentGame, actor: EmploymentPlayer, actionId: unknown): boolean {
  const contract = findEmployment(game, actionId);
  if (!contract || contract.status !== "PENDING" || contract.waiting_on_id !== actor.id || !contract.dev_id) return false;
  const employerId = contract.is_application ? contract.target_id : contract.initiator_id;
  const workerId = contract.is_application ? contract.initiator_id : contract.target_id;
  const development = game.developments.get(contract.dev_id);
  const worker = workerId ? game.players.get(workerId) : undefined;
  if (!employerId || !development || development.owner_id !== employerId || !worker) return false;
  contract.status = "ACCEPTED";
  contract.waiting_on_id = null;
  worker.availableWork.push({
    development,
    wage: contract.wage ?? 0,
    wage_type: contract.wage_type ?? "food",
    employer_id: employerId,
    action_id: contract.id,
  });
  return true;
}

function findEmployment(game: EmploymentGame, actionId: unknown): EmploymentActionDTO | undefined {
  if (typeof actionId !== "string") return undefined;
  for (const player of game.players.values()) {
    const action = player.actions.find((candidate) => candidate.id === actionId);
    if (action?.type === "EMPLOYMENT") return action as EmploymentActionDTO;
  }
  return undefined;
}

export function handleTradeAction(
  game: TradeGame,
  player: TradePlayer,
  command: unknown,
  payload: Record<string, unknown>,
): boolean {
  if (command === "TRADE") return draftTrade(game, player, payload);
  if (command === "ACCEPT") return acceptTrade(game, player, payload.action_id);
  if (command === "BARTER") return barterTrade(game, player, payload);
  if (command === "CANCEL") return cancelTrade(game, player, payload.action_id);
  if (command === "DENY") return denyTrade(game, player, payload.action_id);
  if (command === "FINALIZE") return finalizeTrade(game, player, payload.action_id, payload.actual_items);
  return false;
}

function draftTrade(game: TradeGame, initiator: TradePlayer, payload: Record<string, unknown>): boolean {
  if (typeof payload.target_id !== "string") return false;
  const target = game.players.get(payload.target_id);
  if (!target) return false;
  const parsed = tradeActionSchema.safeParse({
    id: randomUUID(),
    initiator_id: initiator.id,
    target_id: target.id,
    type: "TRADE",
    status: "PENDING",
    waiting_on_id: target.id,
    offer_items: payload.offer_items ?? {},
    request_items: payload.request_items ?? {},
    actual_offer_items: payload.offer_items ?? {},
    actual_request_items: payload.request_items ?? {},
    initiator_finalized: false,
    target_finalized: false,
  });
  if (!parsed.success) return false;
  initiator.actions.push(parsed.data);
  target.actions.push(parsed.data);
  return true;
}

function acceptTrade(game: TradeGame, actor: TradePlayer, actionId: unknown): boolean {
  const trade = findTrade(game, actionId);
  if (!trade || trade.status !== "PENDING" || trade.waiting_on_id !== actor.id) return false;
  trade.status = "ACCEPTED";
  trade.waiting_on_id = null;
  return true;
}

function barterTrade(game: TradeGame, actor: TradePlayer, payload: Record<string, unknown>): boolean {
  const trade = findTrade(game, payload.action_id);
  if (!trade || trade.status !== "PENDING" || trade.waiting_on_id !== actor.id) return false;
  const offerItems = parseItems(payload.offer_items);
  const requestItems = parseItems(payload.request_items);
  if (!offerItems || !requestItems) return false;
  trade.offer_items = offerItems;
  trade.request_items = requestItems;
  trade.waiting_on_id = actor.id === trade.initiator_id ? trade.target_id ?? null : trade.initiator_id;
  return true;
}

function cancelTrade(game: TradeGame, actor: TradePlayer, actionId: unknown): boolean {
  const trade = findTrade(game, actionId);
  if (!trade || trade.status !== "PENDING" || trade.initiator_id !== actor.id) return false;
  trade.status = "CANCELED";
  trade.waiting_on_id = null;
  return true;
}

function denyTrade(game: TradeGame, actor: TradePlayer, actionId: unknown): boolean {
  const trade = findTrade(game, actionId);
  if (!trade || trade.status !== "PENDING" || trade.waiting_on_id !== actor.id) return false;
  trade.status = "DENIED";
  trade.waiting_on_id = null;
  return true;
}

function finalizeTrade(
  game: TradeGame,
  actor: TradePlayer,
  actionId: unknown,
  actualItems: unknown,
): boolean {
  const trade = findTrade(game, actionId);
  if (!trade || trade.status !== "ACCEPTED") return false;
  const parsedItems = parseItems(actualItems);
  if (!parsedItems) return false;
  if (actor.id === trade.initiator_id) {
    if (trade.initiator_finalized) return false;
    trade.actual_offer_items = parsedItems;
    trade.initiator_finalized = true;
  } else if (actor.id === trade.target_id) {
    if (trade.target_finalized) return false;
    trade.actual_request_items = parsedItems;
    trade.target_finalized = true;
  } else {
    return false;
  }
  if (!trade.initiator_finalized || !trade.target_finalized) return true;
  if (!executeTrade(game, trade)) return false;
  trade.status = "COMPLETED";
  return true;
}

function findTrade(game: TradeGame, actionId: unknown): TradeActionDTO | undefined {
  if (typeof actionId !== "string") return undefined;
  for (const player of game.players.values()) {
    const action = player.actions.find((candidate) => candidate.id === actionId);
    if (action?.type === "TRADE") return action as TradeActionDTO;
  }
  return undefined;
}

function parseItems(value: unknown): PartialResourceBundle | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const items = value as Record<string, unknown>;
  for (const [resource, amount] of Object.entries(items)) {
    if (!(["wood", "food", "iron"] as string[]).includes(resource)
      || typeof amount !== "number"
      || !Number.isFinite(amount)
      || amount < 0) return null;
  }
  return items as PartialResourceBundle;
}

function executeTrade(game: TradeGame, trade: TradeActionDTO): boolean {
  const initiator = game.players.get(trade.initiator_id);
  const target = trade.target_id ? game.players.get(trade.target_id) : undefined;
  if (!initiator || !target) return false;
  if (initiator.tradeHistory.some((entry) => entry.id === trade.id)
    || target.tradeHistory.some((entry) => entry.id === trade.id)) return false;

  const sent = transferOut(initiator, trade.actual_offer_items ?? {});
  const received = transferOut(target, trade.actual_request_items ?? {});
  transferIn(target, sent);
  transferIn(initiator, received);
  initiator.tradeHistory.push({
    id: trade.id,
    initiator_id: initiator.id,
    target_id: target.id,
    offered: trade.offer_items ?? {},
    requested: trade.request_items ?? {},
    actual_sent: sent,
    actual_received: received,
  });
  target.tradeHistory.push({
    id: trade.id,
    initiator_id: target.id,
    target_id: initiator.id,
    offered: trade.request_items ?? {},
    requested: trade.offer_items ?? {},
    actual_sent: received,
    actual_received: sent,
  });
  return true;
}

function transferOut(player: TradePlayer, items: PartialResourceBundle): PartialResourceBundle {
  const transferred: PartialResourceBundle = {};
  for (const [resource, requested] of Object.entries(items)) {
    const available = player.resources[resource] ?? 0;
    const amount = Math.min(requested ?? 0, available);
    transferred[resource as keyof PartialResourceBundle] = amount;
    player.resources[resource] = available - amount;
  }
  return transferred;
}

function transferIn(player: TradePlayer, items: PartialResourceBundle): void {
  for (const [resource, amount] of Object.entries(items)) {
    player.resources[resource] = (player.resources[resource] ?? 0) + (amount ?? 0);
  }
}
