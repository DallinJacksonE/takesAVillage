import { randomUUID } from "node:crypto";

import {
  gameStateSchema,
  type ChatDTO,
  type ChatMessageDTO,
  type GameStateDTO,
  type MapTileDTO,
  type PlayerDTO,
  type ResourceBundle,
} from "@takes-a-village/shared";

import { DEFAULT_RULES, RULESETS, type RulesetName } from "./rules.js";
import { cleanupCampfireActions, handleCampfireAction } from "./actions/campfire.js";
import {
  activatePendingContests,
  handleContestAction,
  resolveContests,
  type ContestDevelopment,
} from "./actions/conflict.js";
import { handleEmploymentAction, handleTradeAction } from "./actions/contracts.js";
import { degradeDevelopments, handleDevelopmentAction } from "./actions/development.js";
import { resolveNightPlayers } from "./actions/night.js";
import { handleWorkAction, resolveWork } from "./actions/work.js";

export type PhaseCompletedCallback = (game: Game, phase: GameStateDTO["phase"]) => void | Promise<void>;

export interface GameCreationMetadata {
  trainingSessionId?: string | null;
  trainingGeneration?: number | null;
  onPhaseCompleted?: PhaseCompletedCallback;
}

export class Player {
  readonly actions: PlayerDTO["actions"] = [];
  readonly timeline: PlayerDTO["timeline"] = [];
  readonly developments: string[] = [];
  readonly availableWork: PlayerDTO["available_work"] = [];
  readonly tradeHistory: NonNullable<PlayerDTO["trade_history"]> = [];
  readonly fireHistory: NonNullable<PlayerDTO["fire_history"]> = [];
  health: PlayerDTO["health"] = "healthy";
  fireStatus: PlayerDTO["fire_status"] = "COLD";
  fireGuests: string[] = [];
  finishedPhase = false;
  committedAction: PlayerDTO["committed_action"] = null;

  constructor(
    readonly id: string,
    readonly name: string,
    readonly resources: ResourceBundle,
    public sicknessChance: number,
  ) {}

  toDTO(): PlayerDTO {
    return {
      id: this.id,
      name: this.name,
      health: this.health,
      sickness_chance: this.sicknessChance,
      fire_status: this.fireStatus,
      fire_guests: [...this.fireGuests],
      resources: { ...this.resources },
      developments: [...this.developments],
      available_work: [...this.availableWork],
      committed_action: this.committedAction,
      actions: [...this.actions],
      timeline: [...this.timeline],
      finished_phase: this.finishedPhase,
      trade_history: [...this.tradeHistory],
      fire_history: [...this.fireHistory],
    };
  }
}

export class Game {
  readonly players = new Map<string, Player>();
  readonly developments = new Map<string, ContestDevelopment>();
  readonly chatMessages: ChatMessageDTO[] = [];
  readonly chats: ChatDTO[] = [];
  readonly rules;
  status: GameStateDTO["status"] = "WAITING";
  hostConnected = false;
  day = 1;
  phase: GameStateDTO["phase"] = "WORK";
  phaseEndTime = 0;
  mapData: Record<string, MapTileDTO> = {};
  gameLength: number;
  readonly trainingSessionId: string | null;
  readonly trainingGeneration: number | null;
  tradeCount = 0;
  contestCount = 0;
  readonly lieCount = new Map<string, number>();
  readonly mapHistory: Record<string, GameStateDTO["map"]> = {};
  readonly playerHistory: Record<string, Record<string, ReturnType<Player["toDTO"]>>> = {};
  private readonly onPhaseCompleted: PhaseCompletedCallback;
  private readonly pendingPhaseCompletions = new Set<Promise<void>>();

  constructor(
    readonly id: string,
    readonly hostId: string,
    rulesetName: string = "default",
    readonly botCount = 0,
    readonly training = false,
    private readonly clock: () => number = () => Date.now() / 1000,
    metadata: GameCreationMetadata = {},
  ) {
    this.rules = RULESETS[rulesetName as RulesetName] ?? DEFAULT_RULES;
    this.gameLength = this.rules.GAME_LENGTH;
    this.trainingSessionId = metadata.trainingSessionId ?? null;
    this.trainingGeneration = metadata.trainingGeneration ?? null;
    this.onPhaseCompleted = metadata.onPhaseCompleted ?? (() => undefined);
  }

  addPlayer(id: string): Player {
    const existing = this.players.get(id);
    if (existing) return existing;
    const name = this.rules.AVAILABLE_NAMES[this.players.size % this.rules.AVAILABLE_NAMES.length] ?? `Player ${this.players.size + 1}`;
    const player = new Player(id, name, { ...this.rules.STARTING_INVENTORY }, this.rules.DEFAULT_SICKNESS);
    this.players.set(id, player);
    return player;
  }

  removePlayer(id: string): void {
    this.players.delete(id);
  }

  startGame(): boolean {
    if (this.status !== "WAITING" || this.players.size < 1) return false;
    this.status = "RUNNING";
    this.phase = "WORK";
    this.phaseEndTime = this.clock() + this.rules.PHASE_LENGTH;
    this.mapData = createMap(this.players.size, this.rules.FARMS_RATIO, this.rules.WOODS_RATIO, this.rules.MOUNTAINS_RATIO);
    for (const player of this.players.values()) player.finishedPhase = false;
    return true;
  }

  handleAction(playerId: string, action: unknown): boolean {
    const player = this.players.get(playerId);
    if (!player || !action || typeof action !== "object") return false;
    const candidate = action as { action_command?: unknown; payload?: unknown };
    if (player.health === "dead") return false;
    if (player.finishedPhase && ![
      "FINISH_PHASE",
      "ACCEPT",
      "DENY",
      "CANCEL",
      "BARTER",
      "FINALIZE",
    ].includes(String(candidate.action_command))) return false;
    const payload = candidate.payload && typeof candidate.payload === "object"
      ? candidate.payload as Record<string, unknown>
      : {};
    let accepted = false;
    if (candidate.action_command === "BUILD_DEV") accepted = this.buildDevelopment(player, payload.tile_id);
    else if (candidate.action_command === "START_FIRE") accepted = this.startFire(player);
    else if (candidate.action_command === "FINISH_PHASE") {
      player.finishedPhase = true;
      accepted = true;
    }
    else accepted = handleCampfireAction(this, player, candidate.action_command, payload)
      || handleContestAction(this, player, candidate.action_command, payload)
      || handleDevelopmentAction(this, player, candidate.action_command, payload)
      || handleWorkAction(this, player, candidate.action_command, payload)
      || handleEmploymentAction(this, player, candidate.action_command, payload)
      || handleTradeAction(this, player, candidate.action_command, payload);
    if (accepted) this.checkAllPlayersLocked();
    return accepted;
  }

  nextPhase(): void {
    if (this.status !== "RUNNING") return;
    const completion = this.onPhaseCompleted(this, this.phase);
    if (completion) {
      const tracked = Promise.resolve(completion).finally(() => this.pendingPhaseCompletions.delete(tracked));
      this.pendingPhaseCompletions.add(tracked);
      void tracked.catch(() => undefined);
    }
    if (this.phase === "WORK") {
      resolveContests(this);
      resolveWork(this);
      this.phase = "TRADE";
    }
    else if (this.phase === "TRADE") this.phase = "NIGHT";
    else {
      this.captureHistory();
      if (this.day >= this.gameLength) {
        this.status = "ENDED";
        return;
      }
      cleanupCampfireActions(this);
      this.consumeNight();
      degradeDevelopments(this);
      this.day += 1;
      this.phase = "WORK";
      activatePendingContests(this);
    }
    for (const player of this.players.values()) {
      player.finishedPhase = player.health === "dead";
      player.fireGuests = [];
    }
    this.phaseEndTime = this.clock() + this.rules.PHASE_LENGTH;
  }

  checkAllPlayersLocked(): void {
    const living = [...this.players.values()].filter((player) => player.health !== "dead");
    if (living.length > 0 && living.every((player) => player.finishedPhase)) this.nextPhase();
  }

  checkTimer(): boolean {
    if (this.status === "RUNNING" && this.clock() >= this.phaseEndTime) {
      this.nextPhase();
      return true;
    }
    return false;
  }

  private buildDevelopment(player: Player, tileId: unknown): boolean {
    if (this.status !== "RUNNING" || this.phase !== "WORK" || typeof tileId !== "string") return false;
    const tile = this.mapData[tileId];
    if (!tile || tile.development) return false;
    const costs = this.rules.DEVELOPMENT_COSTS[tile.type].build;
    if (!canAfford(player.resources, costs)) return false;
    spend(player.resources, costs);
    const id = `d_${randomUUID().replaceAll("-", "").slice(0, 8)}`;
    const opposite = tile.type === "Farm" ? "wood" : tile.type === "Woods" ? "food" : undefined;
    const development: ContestDevelopment = {
      id,
      type: tile.type,
      level: 2,
      maintenance_days: this.rules.MAINTENANCE_DAYS,
      owner_id: player.id,
      is_contested: false,
      contest_initiator_id: null,
      contester_supporters: [],
      owner_supporters: [],
      maintenance_cost: opposite ? { [opposite]: 2, iron: 1 } : { food: 5, wood: 5 },
      upgrade_cost: opposite ? { [opposite]: 5, iron: 2 } : { food: 2, wood: 2, iron: 5 },
      can_upgrade: true,
      pending_contest: false,
    };
    this.developments.set(id, development);
    this.mapData[tileId] = { ...tile, development };
    player.developments.push(id);
    player.finishedPhase = true;
    return true;
  }

  private startFire(player: Player): boolean {
    if (this.status !== "RUNNING" || this.phase !== "NIGHT" || player.fireStatus === "HOST") return false;
    if (!canAfford(player.resources, this.rules.CAMPFIRE_COST)) return false;
    spend(player.resources, this.rules.CAMPFIRE_COST);
    player.fireStatus = "HOST";
    return true;
  }

  private consumeNight(): void {
    resolveNightPlayers(this);
  }

  private captureHistory(): void {
    const day = String(this.day);
    this.mapHistory[day] = structuredClone(this.mapData);
    this.playerHistory[day] = Object.fromEntries(
      [...this.players].map(([playerId, player]) => [playerId, player.toDTO()]),
    );
  }

  async waitForPhaseCompletions(): Promise<void> {
    await Promise.all([...this.pendingPhaseCompletions]);
  }

  getPrivateChatHistory(playerId: string): ChatMessageDTO[] {
    const groupIds = new Set(this.chats.filter((chat) => chat.member_ids.includes(playerId)).map((chat) => chat.id));
    return this.chatMessages.filter((message) => message.to_id === "GLOBAL" || message.to_id === playerId || message.from_id === playerId || (message.to_id ? groupIds.has(message.to_id) : false));
  }

  getStateForPlayer(playerId: string): GameStateDTO | null {
    const player = this.players.get(playerId);
    if (!player) return null;
    return gameStateSchema.parse({
      status: this.status,
      is_host: playerId === this.hostId,
      host_connected: this.hostConnected,
      me: player.toDTO(),
      day: this.day,
      game_length: this.gameLength,
      phase: this.phase,
      time_remaining: Math.max(0, Math.trunc(this.phaseEndTime - this.clock())),
      player_list: [...this.players.values()].map((item) => item.toDTO()),
      map: this.mapData,
      developments: [...this.developments.values()],
      chats: this.chats.filter((chat) => chat.member_ids.includes(playerId)),
      development_costs: this.rules.DEVELOPMENT_COSTS,
      max_fire_seats: this.rules.MAX_FIRE_SEATS,
      campfire_cost: this.rules.CAMPFIRE_COST,
      session_id: playerId,
      cold_sickness_rate: this.rules.COLD_SICKNESS_INCREASE,
      hunger_sickness_rate: this.rules.HUNGER_SICKNESS_INCREASE,
      recovery_rate: this.rules.RECOVERY_RATE,
      training: this.training,
    });
  }

  handleChat(playerId: string, content: unknown, toId: unknown): ChatMessageDTO | null {
    if (typeof content !== "string" || !content.trim() || typeof toId !== "string" || !this.players.has(playerId)) return null;
    const group = this.chats.find((chat) => chat.id === toId);
    if (group ? !group.member_ids.includes(playerId) : toId !== "GLOBAL" && !this.players.has(toId)) return null;
    const message = { id: randomUUID(), from_id: playerId, to_id: toId, content: content.trim(), timestamp: this.clock() } satisfies ChatMessageDTO;
    this.chatMessages.push(message);
    return message;
  }

  createChat(playerId: string, name: unknown, memberIds: unknown): boolean {
    if (typeof name !== "string" || !name.trim() || !Array.isArray(memberIds) || !this.players.has(playerId)) return false;
    if (memberIds.some((id) => typeof id !== "string" || !this.players.has(id))) return false;
    const members = [...new Set([playerId, ...memberIds as string[]])];
    this.chats.push({ id: `c_${randomUUID().slice(0, 8)}`, name: name.trim(), creator_id: playerId, member_ids: members });
    return true;
  }
}

function createMap(playerCount: number, farmsRatio: number, woodsRatio: number, minesRatio: number): Record<string, MapTileDTO> {
  const types: MapTileDTO["type"][] = [
    ...Array(Math.max(Math.trunc(playerCount * farmsRatio), 1)).fill("Farm"),
    ...Array(Math.max(Math.trunc(playerCount * woodsRatio), 1)).fill("Woods"),
    ...Array(Math.max(Math.trunc(playerCount * minesRatio), 1)).fill("Mine"),
  ];
  return Object.fromEntries(types.map((type, index) => {
    const id = `t_${index}_0`;
    return [id, { id, q: index, r: 0, type, development: null } satisfies MapTileDTO];
  }));
}

function canAfford(resources: ResourceBundle, costs: Partial<ResourceBundle>): boolean {
  return Object.entries(costs).every(([resource, amount]) => resources[resource as keyof ResourceBundle] >= (amount ?? 0));
}

function spend(resources: ResourceBundle, costs: Partial<ResourceBundle>): void {
  for (const [resource, amount] of Object.entries(costs)) resources[resource as keyof ResourceBundle] -= amount ?? 0;
}
