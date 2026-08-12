export const GENOME_FIELDS = [
  "food_weight", "wood_weight", "iron_weight", "food_desperation_weight",
  "wood_desperation_weight", "iron_desperation_weight", "survival_weight",
  "growth_weight", "reputation_weight", "aggression_weight", "cooperation_weight",
  "risk_weight", "farm_preference", "woods_preference", "mine_preference",
  "build_weight", "upgrade_weight", "maintain_weight", "contest_weight", "work_weight",
  "fire_weight", "immediate_reward_weight", "future_reward_weight", "greed_weight",
  "friendship_weight", "trust_weight", "generosity_weight", "trade_sympathy_weight",
  "initial_friendship", "initial_generosity", "initial_trust", "initial_greed",
  "friendship_sensitivity", "generosity_sensitivity", "trust_sensitivity",
  "greed_sensitivity", "honest_trust_increase", "honest_friendship_increase",
  "fire_trust_weight", "fire_friendship_weight", "fire_sympathy_weight",
  "fire_trust_sensitivity", "fire_friendship_sensitivity", "fire_generosity_sensitivity",
  "fire_greed_sensitivity", "target_farm_count", "target_woods_count",
  "target_mine_count", "upgrade_bias", "maintain_bias",
] as const;

export const GOAP_GENOME_FIELDS = [
  "food_weight", "wood_weight", "iron_weight", "food_desperation_weight",
  "wood_desperation_weight", "iron_desperation_weight", "warmth_desperation_weight",
  "sickness_desperation_weight", "resource_urgency_curve", "survival_urgency_weight",
  "health_risk_weight", "maintenance_urgency_weight", "survival_weight", "growth_weight",
  "reputation_weight", "aggression_weight", "cooperation_weight", "risk_weight",
  "trade_deception_weight", "wage_deception_weight", "farm_preference", "woods_preference",
  "mine_preference", "build_weight", "upgrade_weight", "maintain_weight", "contest_weight",
  "work_weight", "fire_weight", "fire_host_weight", "fire_guest_weight",
  "immediate_reward_weight", "future_reward_weight", "production_discount_weight",
  "trade_fairness_weight", "employment_wage_weight", "employer_exploitation_weight",
  "campfire_accept_weight", "finalize_honesty_weight", "tie_break_weight",
  "action_cost_weight", "trust_weight", "fairness_weight", "generosity_weight",
  "hostility_aversion_weight", "reciprocity_weight", "gift_gratitude_weight",
  "betrayal_sensitivity_weight", "forgiveness_weight", "retaliation_weight",
  "planning_depth_weight",
] as const;

export type Genome = Record<string, number>;
export type RandomSource = () => number;

export function genomeFieldsForModel(botModel: string): readonly string[] {
  return botModel === "GOAPGenetic" ? GOAP_GENOME_FIELDS : GENOME_FIELDS;
}

function clampGoap(value: number): number { return Math.max(-1, Math.min(1, value)); }

export function randomGenomeForModel(botModel: string, random: RandomSource = Math.random): Genome {
  const goap = botModel === "GOAPGenetic";
  return Object.fromEntries(genomeFieldsForModel(botModel).map((field) => [field, goap ? random() * 2 - 1 : random() * 3]));
}

export function normalizeGenomeForModel(botModel: string, genome: Record<string, unknown> | null | undefined): Genome {
  return Object.fromEntries(genomeFieldsForModel(botModel).map((field) => {
    const value = typeof genome?.[field] === "number" ? genome[field] : 0;
    return [field, botModel === "GOAPGenetic" ? clampGoap(value) : value];
  }));
}

function defaultGaussian(random: RandomSource): number {
  const first = Math.max(Number.EPSILON, random());
  return Math.sqrt(-2 * Math.log(first)) * Math.cos(2 * Math.PI * random());
}

export interface MutationOptions {
  mutationStrength?: number;
  mutationRate?: number;
  random?: RandomSource;
  gaussian?: () => number;
}

export function mutateGenomeForModel(botModel: string, genome: Genome, options: MutationOptions = {}): Genome {
  const random = options.random ?? Math.random;
  const gaussian = options.gaussian ?? (() => defaultGaussian(random));
  const strength = options.mutationStrength ?? 0.25;
  const rate = options.mutationRate ?? 0.15;
  return Object.fromEntries(Object.entries(normalizeGenomeForModel(botModel, genome)).map(([field, original]) => {
    const value = random() < rate ? original + gaussian() * strength : original;
    return [field, botModel === "GOAPGenetic" ? clampGoap(value) : value];
  }));
}

export function crossoverGenomesForModel(botModel: string, first: Genome, second: Genome, random: RandomSource = Math.random): Genome {
  const a = normalizeGenomeForModel(botModel, first);
  const b = normalizeGenomeForModel(botModel, second);
  return Object.fromEntries(genomeFieldsForModel(botModel).map((field) => [field, random() < 0.5 ? a[field] : b[field]]));
}
