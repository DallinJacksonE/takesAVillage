import type { DevelopmentCostsDict, PartialResourceBundle, ResourceBundle } from "@takes-a-village/shared";

export const DEFAULT_RULES = {
  DEVELOPMENT_COSTS: {
    Farm: { build: { wood: 2 }, maintain: { wood: 2, iron: 1 }, upgrade: { wood: 5, iron: 2 } },
    Woods: { build: { food: 1, wood: 1 }, maintain: { food: 2, iron: 1 }, upgrade: { food: 5, iron: 2 } },
    Mine: { build: { wood: 2, food: 2 }, maintain: { wood: 3, food: 3 }, upgrade: { wood: 2, food: 2, iron: 5 } },
  } satisfies DevelopmentCostsDict,
  RESOURCE_COSTS: { Woods: "food", Farm: "wood" },
  MAX_DEVELOPMENT_LEVEL: 3,
  MAINTENANCE_DAYS: 7,
  STARTING_INVENTORY: { wood: 4, food: 3, iron: 1 } satisfies ResourceBundle,
  CAMPFIRE_COST: { wood: 1 } satisfies PartialResourceBundle,
  MAX_FIRE_SEATS: 3,
  PHASE_LENGTH: 60,
  GAME_LENGTH: 15,
  AVAILABLE_NAMES: ["Bork", "Torq", "Loki", "Snort", "Smoky", "Larry", "Ig", "Irates", "Kranak", "Areril", "Keenmaw", "Lerk", "Brarx", "Krateges", "Krazz", "Gliregg", "Tresagg", "Meemigg", "Nemarx", "Faril", "Stusz"],
  DEFAULT_SICKNESS: 0.03,
  HUNGER_SICKNESS_INCREASE: 0.2,
  COLD_SICKNESS_INCREASE: 0.1,
  RECOVERY_RATE: 0.07,
  FARMS_RATIO: 0.5,
  WOODS_RATIO: 0.75,
  MOUNTAINS_RATIO: 0.4,
} as const;

export const WEALTHY_RULES = {
  ...DEFAULT_RULES,
  DEVELOPMENT_COSTS: {
    ...DEFAULT_RULES.DEVELOPMENT_COSTS,
    Woods: { build: { food: 1, wood: 1 }, maintain: { food: 2, iron: 2 }, upgrade: { food: 5, iron: 3 } },
  },
  MAX_DEVELOPMENT_LEVEL: 5,
  STARTING_INVENTORY: { wood: 5, food: 4, iron: 2 },
} as const;

export const RULESETS = { default: DEFAULT_RULES, wealthy: WEALTHY_RULES } as const;
export type RulesetName = keyof typeof RULESETS;
