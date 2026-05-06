// --- Core Types ---
export type Resource = "wood" | "food" | "iron";

export interface DevelopmentDTO {
  id: string;
  type: "Farm" | "Woods" | "Mine";
  level: number;
  maintenence_days: number;
  owner_id: string;
}

// Replaces AvailableWorkDTO
export interface WorkAction {
  development: DevelopmentDTO;
  wage: number; // For inherent devs, this can represent the base output (e.g., Lvl 2 Farm = 2)
  wage_type: Resource;
  employer_id: string; // The ID of the player paying the wage (or the worker's own ID if working for themselves)
  message_id?: string; // Optional: Links back to the accepted Employment message, making backend cleanup easy
}

export interface PlayerDTO {
  id: string;
  name: string;
  health: "healthy" | "sick" | "recovering";
  fire_status: "COLD" | "HOST" | "GUEST";
  sickness_chance: number;
  // IMPROVEMENT: Use the Resource type here for strict dictionary mapping
  resources: Record<Resource, number>;
  developments: DevelopmentDTO[];
  available_work: WorkAction[]; // Now houses inherent work AND accepted job offers
  committed_action?: WorkAction; // Set when they lock in their choice for the day
  finished_phase: boolean;
}

export interface MapTileDTO {
  id: string;
  q: number;
  r: number;
  type: "Farm" | "Woods" | "Mine";
  owner_id: string | null;
}

// --- Message DTOs (Discriminated Union) ---

export interface BaseMessageDTO {
  id: string;
  from_id: string;
  to_id: string;
  status:
  | "PENDING"
  | "ACCEPTED"
  | "DENIED"
  | "COMPLETED"
  | "COUNTERED"
  | "BARTERING";
  pending_action_from: string;
  is_system?: boolean;
}

export interface TextMessageDTO extends BaseMessageDTO {
  type: "TEXT";
  content?: string;
}

export interface EmploymentMessageDTO extends BaseMessageDTO {
  type: "EMPLOYMENT";
  dev_id?: string;
  wage_offer?: number;
  wage_type?: Resource; // Updated to strict Resource type
  bartered?: boolean;
}

export interface TradeMessageDTO extends BaseMessageDTO {
  type: "TRADE";
  // IMPROVEMENT: Use strict Resource records instead of generic strings
  offer_items?: Partial<Record<Resource, number>>;
  request_items?: Partial<Record<Resource, number>>;
  actual_offer_items?: Partial<Record<Resource, number>>;
  actual_request_items?: Partial<Record<Resource, number>>;
  sender_finalized?: boolean;
  recipient_finalized?: boolean;
  bartered?: boolean;
}

export interface ShareFireMessageDTO extends BaseMessageDTO {
  type: "FIRE";
  action?: "OFFER" | "REQUEST"; // Strict typing based on our earlier campfire chat
}

export type MessageDTO =
  | TextMessageDTO
  | EmploymentMessageDTO
  | TradeMessageDTO
  | ShareFireMessageDTO;

// --- Core Game DTOs ---

export interface GameStateDTO {
  status: "WAITING" | "ACTIVE" | "FINISHED";
  is_host: boolean;
  me: PlayerDTO;
  day: number;
  phase: "WORK" | "TRADE" | "NIGHT";
  time_remaining: number;
  player_list: PlayerDTO[];
  map: MapTileDTO[];
  messages: MessageDTO[];
  session_id?: string;
}

// ... Rest of your network DTOs (JoinableGameDTO, ConsentDTO, etc.) remain the same

export interface ResearchGameDTO {
  game_id: string;
  finished_at: string;
  data: GameStateDTO;
}

export interface JoinableGameDTO {
  id: string;
  name: string;
  players: string;
  isRejoinable?: boolean;
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

export interface ActiveGamesDTO {
  games: Array<JoinableGameDTO>;
}
