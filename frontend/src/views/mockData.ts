import { GameStateDTO, PlayerDTO } from "../../../dtos"; // Adjust import path as needed

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
    { dev_id: "tile-4" }  // Farm owned by Farmer Fran
  ],
  finished_phase: false,
};

const MOCK_PLAYERS: PlayerDTO[] = [
  MOCK_ME,
  {
    id: "mock-user-2",
    name: "Trader Alice",
    health: "recovering",
    sickness_chance: 0,
    resources: { wood: 20, food: 2, iron: 0 },
    developments: [],
    available_work: [],
    finished_phase: true,
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
  },
  {
    id: "mock-user-5",
    name: "Farmer Fran",
    health: "healthy",
    sickness_chance: 10,
    resources: { wood: 10, food: 30, iron: 5 },
    developments: [{ id: "dev4", type: "Farm", level: 3, maintenence_days: 5, owner_id: "mock-user-5" }],
    available_work: [{ dev_id: "tile-4" }],
    finished_phase: true,
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
  },
  {
    id: "mock-user-7",
    name: "Wanderer Will",
    health: "recovering",
    sickness_chance: 40,
    resources: { wood: 2, food: 2, iron: 2 },
    developments: [],
    available_work: [],
    finished_phase: true,
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
  }
];

export const MOCK_STATE: GameStateDTO = {
  status: "ACTIVE",
  is_host: true,
  me: MOCK_ME,
  day: 4,
  phase: "WORK",
  time_remaining: 180,
  player_list: MOCK_PLAYERS,
  map: [
    { id: "tile-1", q: 0, r: 0, type: "Farm", owner_id: "mock-user-1" },
    { id: "tile-2", q: 1, r: -1, type: "Woods", owner_id: "mock-user-3" },
    { id: "tile-3", q: -1, r: 1, type: "Mine", owner_id: "mock-user-4" },
    { id: "tile-4", q: 0, r: -1, type: "Farm", owner_id: "mock-user-5" },
    { id: "tile-5", q: 2, r: 0, type: "Mine", owner_id: "mock-user-8" },
  ],
  messages: [
    {
      id: "msg1",
      from_id: "mock-user-2",
      to_id: "mock-user-1",
      status: "PENDING",
      pending_action_from: "mock-user-1",
      type: "TEXT",
      content: "Do you have any spare food?"
    } as any
  ],
};
