import {
  GameStateDTO,
  PlayerDTO,
  MapTileDTO,
  ActionDTO,
  ChatMessageDTO,
  DevelopmentCostConfig,
  DevelopmentCostsDict
} from "../../../dtos/index"; // Ensure this path is correct for your project

// --------------------------------------------------------
// 1. BASE ENTITIES (Map & Chat)
// --------------------------------------------------------

export const MOCK_MAP: MapTileDTO[] = [
  { id: "tile-1", q: 0, r: 0, type: "Farm", owner_id: "mock-user-1" },
  { id: "tile-2", q: 1, r: -1, type: "Woods", owner_id: "mock-user-3" },
  { id: "tile-3", q: -1, r: 1, type: "Mine", owner_id: "mock-user-4" },
  { id: "tile-4", q: -1, r: 0, type: "Farm" },
  { id: "tile-5", q: -1, r: -1, type: "Woods" },
  { id: "tile-6", q: 0, r: -1, type: "Woods" },
  { id: "tile-7", q: 0, r: 1, type: "Mine" },
];

const MOCK_CHATS: ChatMessageDTO[] = [
  {
    id: "chat-1",
    from_id: "mock-user-2",
    to_id: "GLOBAL",
    content: "Does anyone have spare wood? I am freezing!",
    timestamp: Date.now() - 60000,
  },
  {
    id: "chat-2",
    from_id: "mock-user-3",
    to_id: "mock-user-1",
    content: "I'll trade you wood for food next phase.",
    timestamp: Date.now() - 30000,
  }
];

// --------------------------------------------------------
// 2. PHASE-SPECIFIC ACTIONS (The Contracts)
// --------------------------------------------------------

const WORK_ACTIONS: ActionDTO[] = [
  {
    id: "action-work-1",
    type: "EMPLOYMENT",
    initiator_id: "mock-user-2",
    target_id: "mock-user-1", // They applied to work at your Farm
    dev_id: "tile-1",
    wage: 2,
    wage_type: "food",
    is_application: true,
    status: "PENDING"
  },
  {
    id: "action-work-2",
    type: "EMPLOYMENT",
    initiator_id: "mock-user-1",
    target_id: "mock-user-3", // You offered them a job
    dev_id: "tile-2",
    wage: 1,
    wage_type: "wood",
    is_application: false,
    status: "ACCEPTED" // They accepted, waiting for you to commit!
  },
  {
    id: "action-work-3",
    type: "EMPLOYMENT",
    initiator_id: "mock-user-3", // Lumberjack Larry is the initiator
    target_id: "mock-user-1", // He is offering YOU a job
    dev_id: "tile-2", // At his Woods development
    wage: 3,
    wage_type: "wood",
    is_application: false, // This is an offer, not an application
    status: "PENDING" // Waiting for your response (Accept/Deny/Counter)
  }
];
const TRADE_ACTIONS: ActionDTO[] = [
  {
    id: "action-trade-1",
    type: "TRADE",
    initiator_id: "mock-user-1",
    target_id: "mock-user-2",
    offer_items: { food: 2 },
    request_items: { wood: 1 },
    initiator_finalized: false,
    target_finalized: false,
    status: "PENDING",
    waiting_on_id: "mock-user-2"
  }
];

const NIGHT_ACTIONS: ActionDTO[] = [
  {
    id: "action-fire-1",
    type: "CAMPFIRE",
    initiator_id: "mock-user-4", // They are freezing and asking for a seat
    target_id: "mock-user-1",
    is_request: true,
    status: "PENDING"
  }
];

// --------------------------------------------------------
// 3. BASE PLAYERS & CONFIGS
// --------------------------------------------------------

export const MOCK_ME: PlayerDTO = {
  id: "mock-user-1",
  name: "Settler Bob",
  health: "healthy",
  sickness_chance: 0.05,
  fire_status: "COLD",
  resources: { wood: 5, food: 12, iron: 2 },
  developments: [{ id: "tile-1", type: "Farm", level: 2, maintenance_days: 3, owner_id: "mock-user-1" }],
  available_work: [
    { development: { id: "tile-1", type: "Farm", level: 2, maintenance_days: 3, owner_id: "mock-user-1" }, wage: 2, wage_type: "food", employer_id: "mock-user-1" }
  ],
  committed_action: null,
  actions: [], // Populated dynamically below based on phase
  timeline: [],
  finished_phase: false,
};

const MOCK_OPPONENTS: PlayerDTO[] = [
  { ...MOCK_ME, id: "mock-user-2", name: "Farmer Fran", actions: [] },
  { ...MOCK_ME, id: "mock-user-3", name: "Lumberjack Larry", health: "recovering" },
  { ...MOCK_ME, id: "mock-user-4", name: "Miner Mike", health: "sick" },
];

const MOCK_ECONOMY_CONFIG: Record<"Farm" | "Woods" | "Mine", DevelopmentCostConfig> = {
  Farm: {
    build: { wood: 5 },
    maintain: { wood: 1 },
    upgrade: { wood: 10, iron: 2 }
  },
  Woods: {
    build: { food: 5 },
    maintain: { food: 1 },
    upgrade: { food: 10, iron: 2 }
  },
  Mine: {
    build: { wood: 10, food: 10 },
    maintain: { wood: 2, food: 2 },
    upgrade: { wood: 20, food: 20 }
  }
};

const MOCK_DEV_COSTS: DevelopmentCostsDict = {
  "tile-1": {
    build: { wood: 5, food: 0, iron: 0 },
    maintain: { wood: 1, food: 0, iron: 0 },
    upgrade: { wood: 10, food: 0, iron: 2 }
  }
};

const BASE_STATE: GameStateDTO = {
  status: "ACTIVE",
  is_host: true,
  me: MOCK_ME,
  day: 1,
  phase: "WORK",
  time_remaining: 45,
  player_list: [MOCK_ME, ...MOCK_OPPONENTS],
  map: MOCK_MAP,
  developments: MOCK_ME.developments, // Simplified for mock: just including the single mocked development
  chat_messages: MOCK_CHATS,
  economy_config: MOCK_ECONOMY_CONFIG,
  development_costs: MOCK_DEV_COSTS,
  max_fire_seats: 3,
  campfire_cost: { wood: 2, food: 0, iron: 0 },
};

// --------------------------------------------------------
// 4. EXPORTED MOCK STATES
// --------------------------------------------------------

export const MOCK_STATE_WORK: GameStateDTO = {
  ...BASE_STATE,
  phase: "WORK",
  me: { ...MOCK_ME, actions: WORK_ACTIONS }
};

export const MOCK_STATE_TRADE: GameStateDTO = {
  ...BASE_STATE,
  phase: "TRADE",
  me: { ...MOCK_ME, actions: TRADE_ACTIONS }
};

export const MOCK_STATE_NIGHT: GameStateDTO = {
  ...BASE_STATE,
  phase: "NIGHT",
  me: { ...MOCK_ME, fire_status: "HOST", actions: NIGHT_ACTIONS } // Set to HOST so you can accept requests
};

// Change this line to test different phases in your UI!
export const MOCK_STATE = MOCK_STATE_WORK;
