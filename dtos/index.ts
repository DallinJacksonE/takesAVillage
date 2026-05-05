
export interface AvailableWorkDTO {
  dev_id: string;
}

export interface PlayerDTO {
  id: string;
  name: string;
  health: "healthy" | "sick" | "recovering";
  fire_status: "COLD" | "HOST" | "GUEST";
  sickness_chance: number;
  resources: {
    wood: number;
    food: number;
    iron: number;
  };
  developments: DevelopmentDTO[];
  available_work: AvailableWorkDTO[];
  finished_phase: boolean;
}

export interface DevelopmentDTO {
  id: string;
  type: "Farm" | "Woods" | "Mine";
  level: number;
  maintenence_days: number;
  owner_id: string;
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
  wage_type?: string;
  bartered?: boolean;
}

export interface TradeMessageDTO extends BaseMessageDTO {
  type: "TRADE";
  offer_items?: Record<string, number>;
  request_items?: Record<string, number>;
  actual_offer_items?: Record<string, number>;
  actual_request_items?: Record<string, number>;
  sender_finalized?: boolean;
  recipient_finalized?: boolean;
  bartered?: boolean;
}

export interface ShareFireMessageDTO extends BaseMessageDTO {
  type: "FIRE";
  action?: string;
}

// This union type tells TypeScript that a MessageDTO is exactly ONE of these shapes
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
