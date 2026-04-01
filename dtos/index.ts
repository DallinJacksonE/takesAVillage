export interface PlayerDTO {
  id: string;
  name: string;
  health: "healthy" | "sick";
  sickness_chance: number;
  resources: {
    wood: number;
    food: number;
    iron: number;
  };
  developments: DevelopmentDTO[];
  available_work: string[];
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

export interface MessageDTO {
  id: string;
  from_id: string;
  to_id: string;
  type: "TEXT" | "TRADE" | "EMPLOYMENT";
  content?: string;
  offer_items?: Record<string, number>;
  request_items?: Record<string, number>;
  wage_offer?: number;
  wage_type?: string;
  dev_id?: string;
  status:
    | "PENDING"
    | "ACCEPTED"
    | "DENIED"
    | "COMPLETED"
    | "COUNTERED"
    | "BARTERING";
  is_system?: boolean;
  bartered?: boolean;
  sender_finalized?: boolean;
  recipient_finalized?: boolean;
  actual_items?: Record<string, number>;
  actual_offer_items?: Record<string, number>;
  actual_request_items?: Record<string, number>;
}

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
