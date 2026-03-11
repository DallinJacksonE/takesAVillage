export interface Player {
  id: string;
  name: string;
  health: 'healthy' | 'sick';
  sickness_chance: number;
  resources: {
    wood: number;
    food: number;
    iron: number;
  };
  developments: Development[];
  available_work: string[];
  finished_phase: boolean;
}

export interface Development {
  id: string;
  type: 'Farm' | 'Woods' | 'Mine';
  level: number;
  maintenence_days: number;
  owner_id: string;
}

export interface MapTile {
  id: string;
  q: number;
  r: number;
  type: 'Farm' | 'Woods' | 'Mine';
  owner_id: string | null;
}

export interface Message {
  id: string;
  from_id: string;
  to_id: string;
  type: 'TEXT' | 'TRADE' | 'EMPLOYMENT';
  content?: string;
  offer_items?: Record<string, number>;
  request_items?: Record<string, number>;
  wage_offer?: number;
  wage_type?: string;
  dev_id?: string;
  status: 'PENDING' | 'ACCEPTED' | 'DENIED' | 'BARTERING';
  is_system?: boolean;
}

export interface GameState {
  status: 'WAITING' | 'ACTIVE' | 'FINISHED';
  is_host: boolean;
  me: Player;
  day: number;
  phase: 'WORK' | 'TRADE' | 'NIGHT';
  time_remaining: number;
  player_list: Player[];
  map: MapTile[];
  messages: Message[];
  session_id?: string;
}
