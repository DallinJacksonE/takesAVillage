// mockData.ts
import {
  GameStateDTO,
  PlayerDTO,
  MessageDTO,
  MapTileDTO,
  EmploymentMessageDTO,
  TradeMessageDTO,
  ShareFireMessageDTO
} from "../../../dtos/index"; // Adjust import path as needed

// --------------------------------------------------------
// 1. BASE ENTITIES (Map & Me)
// --------------------------------------------------------

export const MOCK_ME: PlayerDTO = {
  id: "mock-user-1",
  name: "Settler Bob",
  health: "healthy",
  sickness_chance: 15,
  resources: { wood: 5, food: 12, iron: 2 },
  developments: [{ id: "dev1", type: "Farm", level: 1, maintenence_days: 3, owner_id: "mock-user-1" }],
  available_work: [
    { dev_id: "tile-1" },
    { dev_id: "tile-2" },
    { dev_id: "tile-4" }
  ],
  finished_phase: false,
  fire_status: "COLD",
};

export const MOCK_MAP: MapTileDTO[] = [
  { id: "tile-1", q: 0, r: 0, type: "Farm", owner_id: "mock-user-1" },
  { id: "tile-2", q: 1, r: -1, type: "Woods", owner_id: "mock-user-3" },
  { id: "tile-3", q: -1, r: 1, type: "Mine", owner_id: "mock-user-4" },
  { id: "tile-4", q: 0, r: -1, type: "Farm", owner_id: "mock-user-5" },
  { id: "tile-5", q: 1, r: 0, type: "Mine", owner_id: "mock-user-8" },
];

// --------------------------------------------------------
// 2. PLAYERS 
// --------------------------------------------------------

const BASE_PLAYERS: PlayerDTO[] = [
  MOCK_ME,
  {
    id: "mock-user-2",
    name: "Trader Alice",
    health: "recovering",
    sickness_chance: 0,
    resources: { wood: 19, food: 2, iron: 0 },
    developments: [],
    available_work: [],
    finished_phase: true,
    fire_status: "COLD",
  },
  {
    id: "mock-user-3",
    name: "Lumberjack Larry",
    health: "healthy",
    sickness_chance: 5,
    resources: { wood: 50, food: 0, iron: 0 },
    developments: [{ id: "dev2", type: "Woods", level: 2, maintenence_days: 1, owner_id: "mock-user-3" }],
    available_work: [{ dev_id: "tile-2" }],
    finished_phase: false,
    fire_status: "COLD",
  },
  {
    id: "mock-user-4",
    name: "Miner Mike",
    health: "sick",
    sickness_chance: 80,
    resources: { wood: 0, food: 5, iron: 15 },
    developments: [{ id: "dev3", type: "Mine", level: 1, maintenence_days: 0, owner_id: "mock-user-4" }],
    available_work: [],
    finished_phase: false,
    fire_status: "COLD",
  },
  {
    id: "mock-user-5",
    name: "Farmer Fran",
    health: "healthy",
    sickness_chance: 10,
    resources: { wood: 9, food: 30, iron: 5 },
    developments: [{ id: "dev4", type: "Farm", level: 3, maintenence_days: 5, owner_id: "mock-user-5" }],
    available_work: [{ dev_id: "tile-4" }],
    finished_phase: true,
    fire_status: "COLD",
  },
  {
    id: "mock-user-6",
    name: "Smithy Sam",
    health: "healthy",
    sickness_chance: 20,
    resources: { wood: 15, food: 10, iron: 40 },
    developments: [],
    available_work: [],
    finished_phase: false,
    fire_status: "COLD",
  },
  {
    id: "mock-user-7",
    name: "Wanderer Will",
    health: "recovering",
    sickness_chance: 40,
    resources: { wood: 0, food: 2, iron: 2 },
    developments: [],
    available_work: [],
    finished_phase: true,
    fire_status: "COLD",
  },
  {
    id: "mock-user-8",
    name: "Baroness Beatrice",
    health: "healthy",
    sickness_chance: 0,
    resources: { wood: 100, food: 100, iron: 100 },
    developments: [
      { id: "dev5", type: "Mine", level: 3, maintenence_days: 10, owner_id: "mock-user-8" },
      { id: "dev6", type: "Farm", level: 3, maintenence_days: 10, owner_id: "mock-user-8" }
    ],
    available_work: [{ dev_id: "tile-5" }, { dev_id: "tile-1" }],
    finished_phase: false,
    fire_status: "COLD",
  }
];

// --------------------------------------------------------
// 3. PHASE 1: WORK DATA
// --------------------------------------------------------

const WORK_MESSAGES: MessageDTO[] = [
  // 1. Larry applied to work at YOUR Farm
  {
    id: "emp-msg-1",
    type: "EMPLOYMENT",
    from_id: "mock-user-3", // Larry
    to_id: "mock-user-1",   // You
    status: "PENDING",
    pending_action_from: "mock-user-1",
    dev_id: "tile-1",
    wage_offer: 2,
    wage_type: "food",
    bartered: false,
  } as EmploymentMessageDTO,
  // 2. You applied to work at Farmer Fran's Farm and she countered
  {
    id: "emp-msg-2",
    type: "EMPLOYMENT",
    from_id: "mock-user-1", // You
    to_id: "mock-user-5",   // Fran
    status: "BARTERING",
    pending_action_from: "mock-user-1", // Waiting on your response
    dev_id: "tile-4",
    wage_offer: 4,
    wage_type: "food",
    bartered: true,
  } as EmploymentMessageDTO,
];

export const MOCK_STATE_WORK: GameStateDTO = {
  status: "ACTIVE",
  is_host: true,
  me: MOCK_ME,
  day: 4,
  phase: "WORK",
  time_remaining: 180,
  player_list: BASE_PLAYERS,
  map: MOCK_MAP,
  messages: WORK_MESSAGES,
};

// --------------------------------------------------------
// 4. PHASE 2: TRADE DATA
// --------------------------------------------------------

const TRADE_MESSAGES: MessageDTO[] = [
  // 1. Alice sent you a new Trade Offer (Needs your attention)
  {
    id: "trade-msg-1",
    type: "TRADE",
    from_id: "mock-user-2", // Alice
    to_id: "mock-user-1",   // You
    status: "PENDING",
    pending_action_from: "mock-user-1",
    offer_items: { wood: 4 },
    request_items: { food: 2 },
    actual_offer_items: { wood: 4 },
    actual_request_items: { food: 2 },
    sender_finalized: true,
    recipient_finalized: false,
    bartered: false,
  } as TradeMessageDTO,
  // 2. You are bartering with Miner Mike (Waiting on him)
  {
    id: "trade-msg-2",
    type: "TRADE",
    from_id: "mock-user-1", // You
    to_id: "mock-user-4",   // Mike
    status: "BARTERING",
    pending_action_from: "mock-user-4", // Mike needs to respond
    offer_items: { food: 3 },
    request_items: { iron: 2 },
    actual_offer_items: { food: 3 },
    actual_request_items: { iron: 2 },
    sender_finalized: false,
    recipient_finalized: false,
    bartered: true,
  } as TradeMessageDTO,
];

export const MOCK_STATE_TRADE: GameStateDTO = {
  status: "ACTIVE",
  is_host: true,
  me: MOCK_ME,
  day: 4,
  phase: "TRADE",
  time_remaining: 120,
  player_list: BASE_PLAYERS,
  map: MOCK_MAP,
  messages: TRADE_MESSAGES,
};

// --------------------------------------------------------
// 5. PHASE 3: NIGHT DATA
// --------------------------------------------------------

// For Night, we need to inject the fire statuses into the players
const NIGHT_PLAYERS: PlayerDTO[] = BASE_PLAYERS.map(p => {
  if (p.id === "mock-user-2") return { ...p, fire_status: "HOST" }; // Alice is hosting
  if (p.id === "mock-user-3") return { ...p, fire_status: "GUEST" }; // Larry is sitting with Alice
  if (p.id === "mock-user-5") return { ...p, fire_status: "HOST" }; // Fran is hosting
  return { ...p, fire_status: "COLD" };
});

const NIGHT_MESSAGES: MessageDTO[] = [
  // 1. Trader Alice (HOST) offered YOU a seat (Incoming Offer)
  {
    id: "fire-msg-1",
    type: "FIRE",
    action: "OFFER",
    from_id: "mock-user-2",
    to_id: "mock-user-1",
    status: "PENDING",
    pending_action_from: "mock-user-1",
  } as ShareFireMessageDTO,
  // 2. YOU requested a seat from Farmer Fran (Outgoing Request)
  {
    id: "fire-msg-2",
    type: "FIRE",
    action: "REQUEST",
    from_id: "mock-user-1",
    to_id: "mock-user-5",
    status: "PENDING",
    pending_action_from: "mock-user-5",
  } as ShareFireMessageDTO,
  // 3. Trader Alice (HOST) accepted Lumberjack Larry's request (GUEST)
  {
    id: "fire-msg-3",
    type: "FIRE",
    action: "REQUEST",
    from_id: "mock-user-3",
    to_id: "mock-user-2",
    status: "ACCEPTED",
    pending_action_from: "mock-user-3",
  } as ShareFireMessageDTO,
];

export const MOCK_STATE_NIGHT: GameStateDTO = {
  status: "ACTIVE",
  is_host: true,
  me: { ...MOCK_ME, fire_status: "COLD" }, // Ensure you are cold to test the UI
  day: 4,
  phase: "NIGHT",
  time_remaining: 60,
  player_list: NIGHT_PLAYERS,
  map: MOCK_MAP,
  messages: NIGHT_MESSAGES,
};

// ========================================================
// ACTIVE EXPORT: Change this to test different phases
// ========================================================
export const MOCK_STATE: GameStateDTO = MOCK_STATE_TRADE; // Change to MOCK_STATE_TRADE or MOCK_STATE_NIGHT
