// --- Core Types ---
export type Resource = "wood" | "food" | "iron";
export type Phase = "WORK" | "TRADE" | "NIGHT";
export type ActionStatus =
  | "PENDING"
  | "ACCEPTED"
  | "COMMITTED"
  | "DENIED"
  | "CANCELED"
  | "COMPLETED";

export type ResourceBundle = Record<Resource, number>;

export interface DevelopmentActions {
  build: ResourceBundle;
  maintain: ResourceBundle;
  upgrade: ResourceBundle;
}
export type DevelopmentCostsDict = Record<string, DevelopmentActions>;
//

// --- Chat DTO (Pure Social) ---
export interface ChatMessageDTO {
  id: string;
  from_id: string;
  to_id: string; // "GLOBAL" or specific player ID
  content: string;
  timestamp: number;
}

// ------------------------------------
// --- Action DTOs (The Contracts)  ---
// ------------------------------------

export interface BaseActionDTO {
  id: string;
  initiator_id: string;
  target_id?: string; // Made optional for inherent work and system actions
  status: ActionStatus;
}

export interface EmploymentActionDTO extends BaseActionDTO {
  type: "EMPLOYMENT";
  dev_id?: string;
  wage?: number;
  wage_type?: Resource;
  is_application: boolean;
}

export interface TradeActionDTO extends BaseActionDTO {
  type: "TRADE" | "BARTER";
  offer_items?: Partial<ResourceBundle>;
  request_items?: Partial<ResourceBundle>;
  actual_offer_items?: Partial<ResourceBundle>;
  actual_request_items?: Partial<ResourceBundle>;
  initiator_finalized: boolean;
  target_finalized: boolean;
  waiting_on_id: string;
}

export interface TradeHistoryDTO {
  id: string;

  initiator_id: string;
  target_id: string;

  offered: Partial<ResourceBundle>;
  requested: Partial<ResourceBundle>;

  actual_sent: Partial<ResourceBundle>;
  actual_received: Partial<ResourceBundle>
}

export interface CampfireActionDTO extends BaseActionDTO {
  type: "CAMPFIRE" | "START_FIRE";
  is_request: boolean;
}

export interface SystemActionDTO extends BaseActionDTO {
  type: "MAINTENANCE" | "UPGRADE";
  dev_id?: string;
  cost?: number;
  cost_type?: Resource;
}

export interface ContestActionDTO extends BaseActionDTO {
  type: "CONTEST" | "JOIN_CONTEST";
  dev_id: string;
}

// Discriminated Union
export type ActionDTO =
  | EmploymentActionDTO
  | TradeActionDTO
  | CampfireActionDTO
  | SystemActionDTO
  | ContestActionDTO;

// ------------------------------------
// --- WebSocket Payload Envelopes  ---
// ------------------------------------

/**
 * The standard, strict envelope sent to the backend 'submit_action' event.
 * Eliminates backend guessing by enforcing a standard structure.
 */
export interface GameActionPayload<T = any> {
  gameId: string;
  userId: string;
  action_command: string;
  payload: T;
}

// --- Specific Payload Definitions (The "T" in GameActionPayload) ---

export interface BuildDevPayload {
  tile_id: string;
}

export interface TargetDevPayload {
  dev_id: string;
}

export interface ContestDevPayload {
  dev_id: string;
  target_id?: string;
  side?: "INITIATOR" | "CONTESTER" | "OWNER";
}

export interface CommitWorkPayload {
  job: WorkActionDTO;
}

// For ACCEPT, DENY, CANCEL actions
export interface ContractActionPayload {
  action_id: string;
  type?: string;
}

// --- Specific Drafting Payloads ---

export interface DraftTradePayload {
  target_id: string;
  offer_items: Partial<ResourceBundle>;
  request_items: Partial<ResourceBundle>;
  type: "TRADE";
}

export interface CounterTradePayload {
  action_id: string;
  offer_items: Partial<ResourceBundle>;
  request_items: Partial<ResourceBundle>;
}

export interface FinalizeTradePayload {
  action_id: string;
  actual_items: Partial<ResourceBundle>;
}

export interface DraftEmploymentPayload {
  target_id: string;
  dev_id: string;
  wage: number;
  wage_type: Resource;
  is_application: boolean;
  type: "EMPLOYMENT";
}

export interface DraftCampfirePayload {
  target_id: string;
  is_request: boolean;
  type: "CAMPFIRE";
}

// ----------------------
// --- Core Game DTOs ---
// ----------------------

export interface DevelopmentDTO {
  id: string;
  type: "Farm" | "Woods" | "Mine";
  level: number;
  maintenance_days: number;
  owner_id: string;
  is_contested?: boolean;
  contest_initiator_id?: string;
  contester_supporters?: string[];
  owner_supporters?: string[];
}

export interface MapTileDTO {
  id: string;
  q: number;
  r: number;
  type: "Farm" | "Woods" | "Mine";
  development?: DevelopmentDTO;
}

export interface WorkActionDTO {
  development: DevelopmentDTO;
  wage: number;
  wage_type: Resource;
  employer_id: string;
  action_id: string;
}

export interface DevelopmentCostConfig {
  build: Partial<ResourceBundle>;
  maintain: Partial<ResourceBundle>;
  upgrade: Partial<ResourceBundle>;
}

export interface PlayerDTO {
  id: string;
  name: string;
  health: "healthy" | "sick" | "recovering" | "dead";
  sickness_chance: number;
  fire_status: "COLD" | "HOST" | "GUEST";
  fire_guests?: string[];
  resources: ResourceBundle;
  developments: string[];
  available_work: WorkActionDTO[];
  committed_action: WorkActionDTO | ContestActionDTO | null;
  actions: ActionDTO[];
  timeline: any[]; // Lightweight research log left as any[]
  finished_phase: boolean;
  trade_history?: TradeHistoryDTO[];
}

export interface GameStateDTO {
  status: "WAITING" | "ACTIVE" | "ENDED";
  is_host: boolean;
  me: PlayerDTO;
  day: number;
  phase: Phase;
  time_remaining: number;
  player_list: PlayerDTO[];
  map: MapTileDTO[];
  developments: DevelopmentDTO[];
  chat_messages: ChatMessageDTO[];
  economy_config: Record<"Farm" | "Woods" | "Mine", DevelopmentCostConfig>;
  development_costs: DevelopmentCostsDict;
  max_fire_seats: number;
  campfire_cost: ResourceBundle;
  session_id?: string;
}

// --- Network & Lobby DTOs ---

export interface JoinableGameDTO {
  id: string;
  name: string;
  players: string;
  isRejoinable?: boolean;
}

export interface ActiveGamesDTO {
  games: JoinableGameDTO[];
}

export interface ResearchGameDTO {
  game_id: string;
  finished_at: string;
  data: GameStateDTO;
}

export interface NewGameDTO {
  gameId: string;
}

export interface JoinGameDTO {
  gameId: string;
}

export interface ConsentDTO {
  message: string;
  userId: string;
}
