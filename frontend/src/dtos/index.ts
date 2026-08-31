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

export interface GenomeDTO {
  id: number;
  shorthand_name: string;
  name: string;
  genome_data: any;
  created_at: string;
}

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
  content: string;

  // existing
  to_id?: string;

  created_at?: string;
  timestamp?: number;
}

export interface ChatDTO {
  id: string;
  name: string;
  member_ids: string[];
  creator_id: string;
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
  maintenance_cost: Record<string, number>;
  upgrade_cost: Record<string, number>;
  can_upgrade: boolean;
  pending_contest: boolean;
}

export interface MapTileDTO {
  id: string;
  q: number;
  r: number;
  type: "Farm" | "Woods" | "Mine";
  development?: DevelopmentDTO;
}

export type MapDataDTO = MapTileDTO[] | Record<string, MapTileDTO>;

export interface WorkActionDTO {
  development: DevelopmentDTO;
  wage: number;
  wage_type: Resource;
  employer_id: string;
  action_id: string | null;
}

export interface DevelopmentCostConfig {
  build: Partial<ResourceBundle>;
  maintain: Partial<ResourceBundle>;
  upgrade: Partial<ResourceBundle>;
}

export type PlayerVisualAnimation =
  | "IDLE"
  | "WALK"
  | "WORK_FARM"
  | "WORK_WOODS"
  | "WORK_MINE"
  | "BUILD"
  | "CONTEST"
  | "CARRY"
  | "HURT"
  | "SICK"
  | "DEAD";

export type PlayerVisualLocation =
  | { kind: "HOME" }
  | { kind: "TILE"; id: string; slot?: number }
  | { kind: "DEVELOPMENT"; id: string; slot?: number }
  | { kind: "TRADE"; id: string; side: "INITIATOR" | "TARGET" }
  | { kind: "FIRE"; id: string; slot: number }
  | { kind: "NIGHT_COLD"; slot: number };

export interface PlayerVisualStateDTO {
  animation: PlayerVisualAnimation;
  location: PlayerVisualLocation;
}

export interface PublicInteractionDTO {
  id: string;
  kind: "TRADE";
  participant_ids: string[];
  status: "PENDING" | "ACCEPTED" | "FINALIZED" | "DENIED" | "EXPIRED";
}

export interface PublicPlayerDTO {
  id: string;
  name: string;
  health: "healthy" | "sick" | "recovering" | "dead";
  fire_status: "COLD" | "HOST" | "GUEST";
  fire_guests: string[];
  developments: string[];
  finished_phase: boolean;
  phase_state: "ACTIVE" | "INTENT_SUBMITTED" | "NEEDS_REPLACEMENT" | "RESOLVED" | "DEAD";
  visual_state: PlayerVisualStateDTO;
  reaction?: {
    emoji: "👍" | "❤️" | "😂" | "😠";
    expires_at: number;
  } | null;
}

export interface PlayerDTO {
  id: string;
  name: string;
  health: "healthy" | "sick" | "recovering" | "dead";
  sickness_chance: number;
  fire_status: "COLD" | "HOST" | "GUEST";
  fire_guests: string[];
  resources: ResourceBundle;
  developments: string[];
  available_work: WorkActionDTO[];
  committed_action: WorkActionDTO | ContestActionDTO | null;
  actions: ActionDTO[];
  timeline: any[]; // Lightweight research log left as any[]
  finished_phase: boolean;
  phase_state: "ACTIVE" | "INTENT_SUBMITTED" | "NEEDS_REPLACEMENT" | "RESOLVED" | "DEAD";
  trade_history?: TradeHistoryDTO[];
  fire_history?: FireHistoryDTO[];
}

export interface FireHistoryDTO {
  fire_id: string;
  host_id: string;
  role: "host" | "guest";
  guests: Set<string>;
}

export interface GameStateDTO {
  status: "WAITING" | "ACTIVE" | "ENDED";
  state_revision: number;
  is_host: boolean;
  host_connected: boolean;
  me: PlayerDTO;
  day: number;
  phase: Phase;
  time_remaining: number;
  player_list: PublicPlayerDTO[];
  public_interactions: PublicInteractionDTO[];
  map: MapDataDTO;
  developments: DevelopmentDTO[];
  chat_messages: ChatMessageDTO[];

  chats: ChatDTO[];

  development_costs: DevelopmentCostsDict;
  max_fire_seats: number;
  campfire_cost: ResourceBundle;
  session_id?: string;

  cold_sickness_rate: number;
  hunger_sickness_rate: number;
  recovery_rate: number;
  training: boolean;
  night_transition?: {
    id: string;
    deadline: number;
    affected_player_ids: string[];
  };
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

export interface ResearchPlayerSnapshot {
  health: string;
  actions: any[];
  resources: ResourceBundle;
  fire_status: string;
  developments: string[];
  finished_phase: boolean;
  sickness_chance: number;
  committed_action: any;
}

export interface ResearchGameDTO {
  game_id: string;
  day_num: number;
  phase: string;
  created_at: string;
  game_type?: "human" | "human_bot" | "training";
  training_batch_id?: string | null;
  training_generation?: number | null;
  visualizations?: ResearchVisualizationDTO[];

  data: {
    map: Record<
      string, // day
      Record<
        string, // tile id
        MapTileDTO
      >
    >;

    players: Record<
      string, // day
      Record<
        string, // player id
        ResearchPlayerSnapshot
      >
    >;
  };
}

export interface ResearchVisualizationDTO {
  id: string;
  scope_type: "game" | "training_batch";
  scope_id: string;
  name: string;
  title: string;
  mime_type: string;
  url: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface ResearchGameListItemDTO {
  game_id: string;
  day_num: number;
  phase: string;
  created_at: string;
  game_type: "human" | "human_bot" | "training";
  training_batch_id?: string | null;
  training_generation?: number | null;
}

export interface ResearchGameDetailDTO extends ResearchGameDTO {
  visualizations: ResearchVisualizationDTO[];
}

export interface TrainingGenerationStatisticsDTO {
  generation: number;
  best_fitness: number;
  average_fitness: number;
  median_fitness?: number;
  worst_fitness?: number;
  survival_rate?: number;
  average_resources?: number;
  average_developments?: number;
  illegal_action_count?: number;
  gene_diversity?: Record<string, number>;
}

export interface TrainingBatchListItemDTO {
  batch_id: string;
  status: "running" | "completed" | "failed" | "stalled" | "cancelled";
  ruleset?: string;
  bot_model?: string;
  bot_count?: number;
  total_generations?: number;
  current_generation?: number;
  current_game_id?: string | null;
  games_per_generation?: number;
  games_completed?: number;
  games_failed?: number;
  current_generation_game_index?: number;
  phase?: string | null;
  last_error?: string | null;
  last_heartbeat_at?: string | null;
  started_at?: string;
  completed_at?: string | null;
  generation_statistics?: TrainingGenerationStatisticsDTO[];
}

export interface TrainingBatchDetailDTO extends TrainingBatchListItemDTO {
  base_genome_id?: string | null;
  final_champion_genome_id?: string | null;
  config?: Record<string, any>;
  games?: Array<{
    game_id: string;
    generation: number;
    attempt?: number | null;
    status?: "spawning" | "running" | "completed" | "failed" | "skipped";
    error_message?: string | null;
    genome_count?: number;
    best_fitness?: number | null;
    average_fitness?: number | null;
  }>;
  visualizations: ResearchVisualizationDTO[];
}

export interface TrainingSessionDTO {
  session_id: string;
  current_game_id?: string | null;
  ruleset: string;
  bot_count: number;
  generation: number;
  generations_left: number;
  games_per_generation?: number;
  games_completed?: number;
  games_failed?: number;
  current_generation_game_index?: number;
  population_size: number;
  elite_count?: number;
  selection_size?: number;
  mutation_strength?: number;
  mutation_rate?: number;
  random_immigrant_count?: number;
  generation_statistics: TrainingGenerationStatisticsDTO[];
}

export interface TrainingSessionsDTO {
  sessions: TrainingSessionDTO[];
}

export interface NewGameDTO {
  gameId: string;
}

export interface NewGameOptionsDTO {
  options: Record<string, Record<string, any>>;
}

export interface JoinGameDTO {
  gameId: string;
}

export interface ConsentDTO {
  message: string;
  userId: string;
}
