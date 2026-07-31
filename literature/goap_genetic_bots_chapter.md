# GOAP Genetic Bots in Takes a Village

A textbook-style guide to the bot architecture, the math underneath it, and a path toward sentiment-aware social memory.

## Chapter goals

After reading this chapter, you should be able to:

1. Explain how the `GOAPGenetic` bot moves through a sense-think-act loop.
2. Read the genome as a vector of behavioral weights rather than as magic numbers.
3. Understand how GOAP, utility scoring, one-step planning, and genetic algorithms fit together.
4. Identify where the current bot can and cannot remember social history.
5. Design a sentiment matrix that lets bots notice wage cheating, trade cheating, and gifts.
6. See where that sentiment signal should enter perception, goals, action scoring, and fitness.

The main implementation lives in:

- `bots/models/goap_genetic/GOAPGenetic.py`
- `bots/models/goap_genetic/goap_genome.py`
- `bots/models/goap_genetic/perception.py`
- `bots/models/goap_genetic/thinking.py`
- `bots/models/goap_genetic/goals.py`
- `bots/models/goap_genetic/acting.py`
- `bots/models/goap_genetic/goap_actions.py`
- `bots/models/goap_genetic/action_features.py`
- `bots/BaseBot.py`
- `bots/models/genetic/fitness.py`

The older direct-scoring bot is in:

- `bots/models/genetic/GeneticBot.py`
- `bots/models/genetic/Genome.py`
- `bots/models/genetic/Relationship.py`

That older bot is useful historically because it already contains a commented-out first draft of relationship tracking. The GOAP bot is the cleaner architecture to extend.

## 1. The problem these bots are solving

Takes a Village is a repeated social dilemma game. On each day, players pass through:

1. Work phase: build, maintain, upgrade, contest, hire, or commit work.
2. Trade phase: exchange resources and pay wages, with room for deception.
3. Night phase: eat, stay warm, host or join fires, and survive sickness risk.

A good bot must solve several competing problems at once:

- short-term survival: food and warmth matter immediately;
- long-term production: farms, woods, and mines produce future resources;
- social exchange: trades and wages can help or harm;
- deception: players may promise one thing and deliver another;
- opportunity cost: spending wood to build may reduce night survival;
- uncertainty: the best strategy depends on the other agents.

The GOAP genetic bot answers this with a layered architecture:

```text
raw game_state JSON
        |
        v
Perception.sense(...)
        |
        v
Memory: objective facts
        |
        v
Thinker.evaluate_goals(...)
        |
        v
winning GOAPGoal
        |
        v
BaseBot.get_available_actions(...)
        |
        v
legal server actions
        |
        v
Actuator + OneStepPlanner
        |
        v
chosen server action
        |
        v
BaseBot.format_network_payload(...)
```

This is a strong direction because it separates responsibilities:

- `BaseBot` knows what the server legally accepts.
- `Perception` reads facts without preferences.
- `GoalLibrary` defines possible desired states.
- `Thinker` chooses which goal currently matters most.
- `Actuator` tries to satisfy that goal with the available legal actions.
- `ActionFeatureCalculator` describes action consequences.
- `ActionUtilityScorer` converts features into genome-weighted utility.
- `GOAPGenome` stores evolvable weights.

That separation is the key difference between a bot that is debuggable and a bot that becomes a pile of nested `if` statements.

## 2. GOAP in plain language

GOAP means Goal-Oriented Action Planning.

A classic planner has:

- a current world state;
- goals, expressed as desired world states;
- actions, with preconditions and effects;
- a planner that finds a sequence of actions moving the world toward a goal.

A toy example:

```text
Current state:
  food = 0
  wood = 2
  fire_status = COLD

Goal:
  SURVIVE

Candidate actions:
  START_FIRE       effect: warmth = 1, cost: wood
  EMPLOYMENT food  effect: food_delta = 1, cost: time/social exposure
  BUILD_DEV Farm   effect: future food production, cost: wood
```

A full GOAP planner might search several steps deep:

```text
get wood -> build fire -> survive night
get job -> earn food -> eat tomorrow
build farm -> produce food later
```

The current `GOAPGenetic` bot is intentionally simpler. It is a one-step GOAP-style planner. It does not search a multi-action tree. It evaluates the legal actions available right now and asks: which one gives the best progress toward the current goal?

That makes it easier to reason about and safer for a real-time game loop. It also means the bot is reactive rather than deeply strategic. It can value future production, but it does not yet simulate several turns forward.

## 3. The current GOAPGenetic architecture

### 3.1 The master object: `GOAPGenetic`

`GOAPGenetic.choose_action()` is intentionally small:

1. Ignore waiting games, dead bots, and bots that already finished the phase.
2. Sense the world through `Perception`.
3. Let `Thinker` select the highest-utility goal.
4. Ask `BaseBot` for legal actions.
5. Let `Actuator` pick an action for the goal.
6. Clean the payload for the server.

That file is the orchestration layer. It should stay that way. It should not grow trade math, relationship math, or ad-hoc action rules.

### 3.2 Perception: the camera

`Perception.sense(game_state)` turns the raw server DTO into `Memory`.

Important facts it extracts:

- phase, day, game length, health, sickness chance;
- own resources: food, wood, iron;
- fire state and campfire costs;
- player list;
- pending contracts;
- available work;
- owned, unowned, other-player, and contested developments;
- affordable build, maintenance, and upgrade opportunities;
- candidate trade inventory.

The key design rule is that perception should be factual. It should not decide that food is “good,” an enemy is “bad,” or a trade is “fair.” Those are preferences. They belong in goal utility, action features, or genome weights.

This is why a future sentiment matrix should probably enter perception as factual memory:

```text
relationship_memory = {
  other_player_id: {
    trust: ...,
    fairness: ...,
    generosity: ...,
    hostility: ...,
    confidence: ...,
    last_interaction_day: ...
  }
}
```

Perception can expose those facts. The scoring layer decides how much they matter.

### 3.3 Memory: the typed boundary

`Memory` is a dict-compatible wrapper around facts. It gives newer code one documented boundary while preserving existing `memory.get(...)` style.

This matters because social memory can become messy fast. If relationships are added directly to loose dicts everywhere, the bot will become hard to debug. A `Memory` boundary lets you add social facts in one place.

### 3.4 Goals: desired states plus utility

`GoalLibrary` defines goals such as:

- `SURVIVE`
- `SECURE_FOOD`
- `SECURE_WOOD`
- `SECURE_WARMTH`
- `INCREASE_PRODUCTION`
- `PRESERVE_ASSETS`
- `IMPROVE_ASSETS`
- `SECURE_INCOME`
- `RESOLVE_OBLIGATIONS`
- `TRADE_TOWARD_SCARCITY`
- `CONTEST_VALUE`
- `COOPERATE`

Each goal contains:

```text
name: desired label

desired_state: human-readable target facts

utility(memory): how important this goal is right now

is_complete(memory): whether the bot should skip the goal

progress(memory, effects): how much an action advances the goal
```

Example: `SECURE_FOOD` becomes more useful when food is scarce. Its utility uses a resource need curve:

```text
need(resource) = 1 / (current_amount + 1) * positive_multiplier(resource_urgency_curve)
```

So if food is 0:

```text
need(food) = 1 / (0 + 1) = 1.0
```

If food is 9:

```text
need(food) = 1 / (9 + 1) = 0.1
```

This creates diminishing urgency. The first unit of food matters much more than the tenth.

### 3.5 Thinking: choosing the active goal

`Thinker.evaluate_goals(memory)` evaluates every goal:

```text
score(goal) = goal.utility(memory) + tie_break_weight
```

Then it returns the max-scoring goal.

The current `tie_break_weight` is added equally to every goal, so it does not actually break ties between goals. If every goal receives the same constant, the ranking is unchanged:

```text
if A > B, then A + c > B + c
if A = B, then A + c = B + c
```

A more useful tie-breaker would be either:

- a deterministic goal-order priority;
- a tiny per-goal genome weight;
- a tiny random or seeded jitter;
- a learned goal-specific bias vector.

### 3.6 Acting: planning over legal actions

`Actuator.act(...)` receives the winning goal and the legal actions. It tries the winning goal first, then falls back through a fixed goal order.

This fallback is important. A bot may want to expand, but if the only useful action is `START_FIRE`, survival should still be possible. The fallback order starts with survival and warmth, then moves through food, assets, income, obligations, cooperation, production, trade, and contest.

The actual one-step planning happens in `OneStepPlanner`.

## 4. Action templates, features, and utility

### 4.1 Legal actions come from `BaseBot`

`BaseBot.get_available_actions(game_state)` reconstructs possible server actions from the current DTO. It handles:

- `BUILD_DEV`
- `UPGRADE_DEV`
- `MAINTAIN_DEV`
- `CONTEST_DEV`
- `EMPLOYMENT`
- `COMMIT_WORK`
- `TRADE`
- `ACCEPT`
- `DENY`
- `FINALIZE`
- `START_FIRE`
- `CAMPFIRE`

This is a good boundary. The GOAP layer should not invent actions the server will reject.

### 4.2 Action templates bind GOAP meaning to server actions

`ActionTemplate` maps a server command to GOAP effects and costs.

Example templates:

```text
start-fire:
  command: START_FIRE
  effects: warmth = 1, sickness_risk_delta = 1

build-development:
  command: BUILD_DEV
  effects: production_capacity = 1, resource-specific production delta
  cost: build resource cost

accept-contract:
  command: ACCEPT
  effects: cooperation = 1, obligation_resolution = 1
```

A template only binds to legal actions with the matching command. This prevents the planner from choosing imaginary moves.

### 4.3 Features describe facts, not preferences

`ActionFeatureCalculator.calculate(action, memory)` extracts normalized-ish factual features:

- `food_delta`, `wood_delta`, `iron_delta`
- `resource_delta`
- `resource_cost`
- `production_delta`
- `maintenance_days_saved`
- `fire_risk_delta`
- `trade_received_value`
- `trade_given_value`
- `contract_obligation`
- `contested_value`
- `helps_self`
- `helps_other`
- `harms_other`
- `social_exposure`

This is the feature vector:

```text
phi(action, memory) = [food_delta, wood_delta, ..., social_exposure]
```

A feature vector says what an action does. It does not say whether that action is desirable.

### 4.4 The utility dot product

`ActionUtilityScorer` turns features into a score using genome weights.

Mathematically:

```text
feature_utility(action) = sum_i phi_i(action) * w_i
```

Or in vector notation:

```text
U_features(a) = w · phi(a)
```

The planner then combines:

```text
score(action, goal) = goal.progress(memory, action_features) + U_features(action)
```

In code, the candidate is rejected if the total score is negative. The best remaining candidate wins.

This is one of the most important ideas in the bot. The bot is not saying “always build farms” or “always cooperate.” It is saying:

```text
Given my genome weights and this world state, which legal action has the largest weighted utility and goal progress?
```

## 5. The genome as a behavioral vector

`GOAPGenome` is a dataclass of weights in `[-1.0, 1.0]`.

The older `Genome` used random values in `[0, 3]`. The GOAP genome intentionally supports negative genes. This matters because negative genes can express aversion:

```text
cooperation_weight =  1.0  -> likes helping others
cooperation_weight =  0.0  -> neutral
cooperation_weight = -1.0  -> dislikes helping others
```

Gene groups include:

- resource values: food, wood, iron;
- scarcity response: desperation and urgency curves;
- survival and health risk;
- general strategy: survival, growth, reputation;
- personality: aggression, cooperation, risk, deception;
- development preferences;
- action biases;
- time horizon;
- trade, wage, campfire, honesty, and action-cost preferences.

Important helper transforms:

```text
clamp_gene(x) = min(1, max(-1, x))
positive_multiplier(g) = clamp_gene(g) + 1
cost_scale(g) = max(0, clamp_gene(g))
```

So:

```text
positive_multiplier(-1) = 0
positive_multiplier( 0) = 1
positive_multiplier( 1) = 2
```

This lets a gene modulate another term without making it explode.

## 6. Genetic algorithms in this project

A genetic algorithm evolves a population of candidate genomes by repeated evaluation and reproduction.

The project’s training notes describe this lifecycle:

1. Initialize a population.
2. Assign one genome per bot.
3. Let bots play a full game.
4. Calculate each bot’s fitness.
5. Select parents, favoring high fitness.
6. Crossover parent genomes.
7. Mutate the children.
8. Repeat for more generations.

### 6.1 Fitness

`bots/models/genetic/fitness.py` scores completed episodes. The current report includes:

```text
survival
resources
developments_owned
development_levels
maintenance
production
successful_work
profitable_trades
fulfilled_contracts
campfire_cooperation
contest_outcomes
relative_ranking
behavior_penalty
```

The survival score is intentionally dominant:

```text
survival = day * 100
if alive:
  survival += game_length * 100
```

That means a bot that survives longer should beat an early resource hoarder that dies.

### 6.2 Selection

The training notes describe roulette selection. The usual roulette probability is:

```text
P(parent = i) = fitness_i / sum_j fitness_j
```

Higher fitness gives a larger slice of the wheel. A common improvement is rank-based or tournament selection when raw fitness values become too noisy or too dominant.

### 6.3 Crossover

`GOAPGenome.crossover(parent_a, parent_b)` currently chooses each field from either parent at random:

```text
child_gene_k = random_choice(parent_a_gene_k, parent_b_gene_k)
```

This is uniform crossover. It is simple and works well when genes are not strongly position-dependent.

The training notes mention two-point crossover in the service orchestrator. If both exist, it is worth verifying which path is used for GOAP genomes. Uniform crossover is in `GOAPGenome`; orchestrator-level crossover may operate on dicts.

### 6.4 Mutation

`GOAPGenome.mutate(...)` uses Gaussian perturbation:

```text
if random() < mutation_rate:
  gene = gene + Normal(mean=0, std=mutation_strength)
  gene = clamp(gene, -1, 1)
```

With defaults:

```text
mutation_rate = 0.15
mutation_strength = 0.25
```

So each gene has a 15% chance of moving by a random amount centered on zero.

### 6.5 Why genetic learning fits here

This game has many interacting incentives. Hand-tuning every weight is possible, but brittle. Evolution lets you ask:

```text
Which weight vector performs well over many games against many other agents?
```

The weakness is that the bot only optimizes what fitness measures. If fitness rewards resources but not trustworthy relationships, evolution may learn antisocial behavior. If fitness rewards fulfilled contracts and long-term cooperation, evolution can learn more village-like behavior.

## 7. Important current limitations

### 7.1 The GOAP planner is one-step

The current planner does not search action sequences. It evaluates immediate legal actions. Future production is represented by features like `production_delta`, but the bot does not simulate several days ahead.

This is acceptable for now, but it limits deception reasoning. For example, punishing a cheater might be locally costly but strategically useful later. A one-step planner needs explicit relationship features or fitness shaping to value that.

### 7.2 Social memory is not active in GOAP

`GeneticBot.py` has a commented-out relationship system and `Relationship.py` defines:

```text
trust
generosity
friendship
greed
```

But the active GOAP bot does not use that relationship model. Its `Perception` has no persistent cross-turn social memory. It can inspect current contracts and trade history if present, but it does not yet maintain a stable opinion of each other player.

### 7.3 Trade value is currently resource-count based

`ActionFeatureCalculator._add_trade_bundle_features(...)` uses total item counts:

```text
given_total = sum(given.values())
received_total = sum(received.values())
```

That treats 1 food, 1 wood, and 1 iron as equal. But the genome already has resource-specific values. A better trade evaluator should compute subjective value:

```text
value(bundle) = food * food_value + wood * wood_value + iron * iron_value
```

and scarcity-adjusted value:

```text
scarcity_value(bundle) = sum_r amount_r * (base_weight_r + desperation_weight_r / (owned_r + 1))
```

### 7.4 Current trade records need careful interpretation

`service/game/actions/contracts.py` executes trades with capped boxes:

```text
actual_amt = min(requested_amt, current_inventory)
```

The timeline event records the actual capped `sent` and `received` boxes. That is the best source for what truly happened.

The `trade_history` record currently stores `actual_sent` and `actual_received` from the contract’s finalized declarations, not necessarily the capped boxes. If a player declared more than they could afford, the actual inventory transfer may be lower than the trade history suggests. For cheat detection, use the timeline `TRADE_RESOLVED` event or change `trade_history` to store the capped boxes.

### 7.5 Wage payments are modeled as trades

`EmploymentContract._handle_accept(...)` creates a `TradeContract` from employer to worker for bot employers:

```text
TradeContract(employer_id, worker_id, {wage_type: wage_amt}, {})
```

That means wage payment can be analyzed through the same promised-vs-actual machinery as trades, but it should be labeled as a wage. Right now, the generated wage trade does not clearly carry a `reason`, `employment_contract_id`, or `wage_payment` flag. Add that metadata before relying heavily on wage sentiment.

## 8. Designing a sentiment matrix

The user-facing goal is:

> Improve the bots with a sentiment matrix that tracks interactions with other agents and recognizes when they have been cheated in a wage or a trade, and when someone has gifted them something.

The right abstraction is a per-agent relationship vector.

For bot `i` thinking about other player `j`:

```text
S[i, j] = {
  trust:       belief that j honors agreements,
  fairness:   belief that j trades near promised/equitable value,
  generosity: belief that j gives more than required,
  reciprocity: balance of give-and-take over time,
  hostility:  belief that j harms or exploits i,
  affinity:   general positive relationship sentiment,
  confidence: how much evidence supports this estimate,
}
```

This is a sentiment matrix because every bot has a row and every other player has a column:

```text
             about A       about B       about C
bot A          ---          S[A,B]        S[A,C]
bot B        S[B,A]          ---          S[B,C]
bot C        S[C,A]        S[C,B]          ---
```

Each entry is directional. If A thinks B is generous, B does not necessarily think A is generous.

### 8.1 Suggested value ranges

Use bounded values for stability:

```text
trust       in [-1, 1]
fairness    in [-1, 1]
generosity  in [-1, 1]
reciprocity in [-1, 1]
hostility   in [ 0, 1]
affinity    in [-1, 1]
confidence  in [ 0, 1]
```

A neutral new relationship starts near:

```text
trust = 0
fairness = 0
generosity = 0
reciprocity = 0
hostility = 0
affinity = 0
confidence = 0
```

You can add genome genes for initial bias:

```text
initial_trust_bias
forgiveness_weight
betrayal_sensitivity_weight
gift_gratitude_weight
retaliation_weight
relationship_memory_decay
```

## 9. Event classification: cheat, fair trade, gift

The sentiment system should not update directly from action commands. It should update from resolved outcomes.

An accepted trade is only a promise. A finalized trade plus transfer is evidence.

### 9.1 Resource bundle value

For a bundle `b`:

```text
V_i(b) = b_food * W_i_food + b_wood * W_i_wood + b_iron * W_i_iron
```

For scarcity-adjusted value:

```text
Need_i(r) = positive_multiplier(resource_urgency_curve) / (owned_i(r) + 1)

V_i(b) = sum_r b_r * (resource_weight_i(r) + desperation_weight_i(r) * Need_i(r))
```

This makes a gift of food more meaningful to a starving bot than to a rich one.

### 9.2 Promised versus delivered

For a resolved exchange from bot `i`'s perspective:

```text
promised_by_me      = bundle i agreed to send
promised_by_other   = bundle j agreed to send
actual_sent_by_me   = bundle i actually sent
actual_received     = bundle i actually received from j
```

Subjective values:

```text
P_other = V_i(promised_by_other)
D_other = V_i(actual_received)
P_me    = V_i(promised_by_me)
D_me    = V_i(actual_sent_by_me)
```

Shortfall against me:

```text
shortfall = max(0, P_other - D_other)
shortfall_ratio = shortfall / max(P_other, epsilon)
```

Extra received:

```text
surplus_received = max(0, D_other - P_other)
surplus_ratio = surplus_received / max(P_other, epsilon)
```

Net gift value:

```text
gift_value = max(0, D_other - D_me)
```

But gift detection should also inspect intent. A lopsided trade can be a gift, a wage, a correction, or a strategic bribe.

### 9.3 Trade cheating

A player cheated bot `i` in a trade if all are true:

1. There was a promise from `j` to `i`.
2. The actual received value was meaningfully less than promised.
3. The shortfall exceeds a tolerance.

```text
trade_cheated = P_other > 0 and shortfall_ratio > cheat_tolerance
```

Suggested starting tolerance:

```text
cheat_tolerance = 0.10
```

A small mismatch may be inventory capping or rounding. A large mismatch should strongly reduce trust.

### 9.4 Wage cheating

A wage is a special case of promised transfer.

Current implementation creates a wage `TradeContract` from employer to worker. The intended wage is:

```text
promised_wage = {wage_type: wage}
```

If the worker receives less:

```text
wage_shortfall = V_i(promised_wage) - V_i(actual_received)
wage_cheated = wage_shortfall / max(V_i(promised_wage), epsilon) > wage_tolerance
```

Wage cheating should probably hurt trust more than ordinary trade cheating because the worker already spent the work phase producing value for the employer.

Suggested event impact:

```text
trust_delta      -= 0.40 * wage_shortfall_ratio
affinity_delta   -= 0.25 * wage_shortfall_ratio
hostility_delta  += 0.30 * wage_shortfall_ratio
fairness_delta   -= 0.35 * wage_shortfall_ratio
```

### 9.5 Gift recognition

A gift occurs when `j` gives `i` positive value without receiving comparable value and without an existing obligation requiring that transfer.

```text
gift = D_other > 0 and D_me <= gift_return_tolerance * D_other and not is_wage_payment
```

Suggested tolerance:

```text
gift_return_tolerance = 0.25
```

Examples:

- Other sends 3 food and asks for 0: gift.
- Other sends 4 wood and asks for 1 food: generous trade or partial gift.
- Employer pays the agreed wage: not a gift, but trust/fairness positive.
- Employer pays more than wage: wage fulfilled plus gift surplus.

Gift impact:

```text
generosity_delta += 0.35 * normalized_gift_value
trust_delta      += 0.10 * normalized_gift_value
affinity_delta   += 0.25 * normalized_gift_value
reciprocity_delta -= 0.20 * normalized_gift_value  # I now owe them socially
```

The sign of reciprocity depends on convention. One useful convention:

```text
reciprocity > 0: they owe me
reciprocity < 0: I owe them
```

## 10. Updating the sentiment matrix

Do not replace relationship values abruptly. Use an incremental update.

For relationship dimension `x`:

```text
x_{t+1} = clamp((1 - decay) * x_t + alpha * evidence, min, max)
```

Where:

- `decay` slowly forgets old interactions;
- `alpha` controls learning rate;
- `evidence` is the classified event signal;
- `clamp` keeps values bounded.

Confidence can grow with evidence:

```text
confidence_{t+1} = min(1, confidence_t + evidence_strength * confidence_gain)
```

And confidence can scale the impact of relationships in decisions:

```text
relationship_effect = confidence * learned_sentiment_value
```

This prevents one lucky gift or one tiny shortfall from permanently defining a relationship.

### 10.1 A compact update formula

Let event evidence be a vector:

```text
E = [trust_e, fairness_e, generosity_e, reciprocity_e, hostility_e, affinity_e]
```

Let the current sentiment vector be:

```text
S = [trust, fairness, generosity, reciprocity, hostility, affinity]
```

Then:

```text
S' = clamp((1 - decay)S + alpha E)
```

This is easy to test and easy to log.

## 11. How sentiment should affect bot decisions

### 11.1 Perception layer

Add a persistent social model to `GOAPGenetic`:

```text
self.social_memory = SocialMemory()
```

Each call to `choose_action` should:

1. Sense objective game state.
2. Process newly resolved timeline/trade events since the last seen event id.
3. Update `social_memory`.
4. Attach social facts to `Memory`.

Important: track event IDs so the same trade does not update sentiment repeatedly.

### 11.2 Action features

Add relationship features to candidate actions involving another player:

```text
counterparty_trust
counterparty_fairness
counterparty_generosity
counterparty_hostility
counterparty_affinity
counterparty_confidence
expected_cheat_risk
expected_gift_chance
```

For a trade with player `j`:

```text
expected_cheat_risk = confidence(i,j) * max(0, -trust(i,j))
```

For a gift/aid decision:

```text
relationship_goodwill = confidence(i,j) * affinity(i,j)
```

### 11.3 Genome weights

Add genes that say how much the bot cares:

```text
trust_weight
fairness_weight
generosity_weight
hostility_aversion_weight
reciprocity_weight
gift_gratitude_weight
betrayal_sensitivity_weight
forgiveness_weight
retaliation_weight
```

Then action utility can include:

```text
U_social(a, j) =
    trust_weight * trust(i,j)
  + fairness_weight * fairness(i,j)
  + generosity_weight * generosity(i,j)
  - hostility_aversion_weight * hostility(i,j)
  + reciprocity_weight * reciprocity(i,j)
```

For accepting a trade, the bot should discount promised incoming goods by trust:

```text
expected_received_value = promised_received_value * reliability(i,j)
```

A simple reliability function:

```text
reliability(i,j) = clamp(0.5 + 0.5 * trust(i,j), 0, 1)
```

So:

```text
trust = -1 -> reliability = 0
trust =  0 -> reliability = 0.5
trust =  1 -> reliability = 1
```

This makes a known cheater’s promise worth less before the bot accepts the trade.

### 11.4 Goals

Add or modify goals:

```text
AVOID_CHEATERS
RECIPROCATE_KINDNESS
REPAIR_RELATIONSHIP
PUNISH_EXPLOITATION
SEEK_TRUSTED_TRADE
```

But add these carefully. Too many goals can make the planner hard to tune. A cleaner first version is to keep the current goals and add social features to action scoring. Add new goals only after the basic sentiment feature proves useful.

### 11.5 Fitness

Fitness should reward long-term social competence, not just immediate profit.

Add stats such as:

```text
honored_wage_count
wage_shortfall_given
wage_shortfall_received
trade_shortfall_given
trade_shortfall_received
gift_value_given
gift_value_received
trusted_partner_trade_value
repeat_partner_success_count
retaliatory_denial_count maybe later, with care
```

Be careful with incentives. If you reward `gift_value_received` too much, bots may evolve to beg or exploit altruists. If you reward `gift_value_given` too much, bots may evolve to self-sacrifice. Better fitness terms are usually:

```text
net_social_surplus
reliable_partner_network
survival/resource success after social interactions
low victimization rate
low betrayal rate, unless training a deception-specific population
```

## 12. Suggested implementation plan

### Phase 1: Data correctness and event classification

1. Add `reason` metadata to trade contracts:
   - `NORMAL_TRADE`
   - `WAGE_PAYMENT`
   - `GIFT`
   - maybe `REPARATION` later
2. When creating wage trades in `EmploymentContract._handle_accept`, include:
   - `reason = WAGE_PAYMENT`
   - `employment_contract_id`
   - `promised_wage`
3. In `SocialResolvers.execute_trade`, store capped actual boxes in `trade_history`:
   - `actual_sent = initiator_box` for initiator
   - `actual_received = target_box` for initiator
   - mirrored for target
4. Add a pure function that classifies a resolved exchange:
   - fair trade
   - trade cheated me
   - wage cheated me
   - gift received
   - gift given
   - overpayment

Keep this classifier independent of the bot so it can be unit tested.

### Phase 2: Social memory model

Create something like:

```text
bots/models/goap_genetic/social_memory.py
```

Core types:

```text
RelationshipSentiment
SocialEventEvidence
SocialMemory
```

Responsibilities:

- store directional sentiment per player id;
- process resolved event evidence once;
- apply decay/update math;
- expose relationship facts to perception/action scoring;
- serialize if bot state needs to survive process restarts.

### Phase 3: Integrate with `GOAPGenetic`

Add to `GOAPGenetic.__init__`:

```text
self.social_memory = SocialMemory()
```

In `choose_action`:

```text
memory = self.perception.sense(game_state)
self.social_memory.observe(memory, game_state)
memory = memory.with_fact("relationships", self.social_memory.as_memory())
```

`Memory` currently has no `with_fact` helper, but you can add one or construct a new `Memory` from `memory.as_dict()`.

### Phase 4: Add social features to action scoring

Update `ActionFeatureCalculator`:

1. Determine counterparty for `TRADE`, `ACCEPT`, `DENY`, `FINALIZE`, `EMPLOYMENT`, `CAMPFIRE`, and `CONTEST_DEV`.
2. Look up relationship facts.
3. Add factual features:
   - `counterparty_trust`
   - `counterparty_fairness`
   - `counterparty_generosity`
   - `counterparty_hostility`
   - `counterparty_confidence`
   - `expected_cheat_risk`

Update `ActionUtilityScorer.weights()` with genome weights.

### Phase 5: Train and compare

Run two bot populations:

1. Baseline GOAP genetic bots.
2. Sentiment-aware GOAP genetic bots.

Compare:

- survival days;
- resource totals;
- fulfilled contracts;
- wage shortfalls suffered;
- trade shortfalls suffered;
- repeat trades with same partners;
- gifts given/received;
- final relative rank.

The key question is not “does sentiment feel realistic?” The key question is:

```text
Does social memory improve survival and prosperity in a world with deception?
```

## 13. Testing strategy

Write unit tests before wiring it into training.

Recommended tests:

1. Fair trade does not change trust much, maybe slightly positive.
2. Trade shortfall decreases trust and fairness.
3. Wage shortfall decreases trust more than ordinary trade shortfall.
4. Gift increases generosity and affinity.
5. Overpayment on wage is classified as wage fulfilled plus gift surplus.
6. Same timeline event id is processed once.
7. Old relationships decay toward neutral.
8. Low confidence reduces impact on action scoring.
9. A bot accepts an equal trade from a trusted partner over the same trade from a known cheater.
10. Trade history uses actual capped transfer, not just declared finalized items.

## 14. Design warnings

### 14.1 Do not let sentiment become hidden rules

Avoid hardcoded behavior like:

```text
if trust < -0.5: always deny trade
```

Prefer features plus genome weights:

```text
expected_cheat_risk feature * betrayal_sensitivity_weight
```

That lets evolution discover whether distrust should dominate.

### 14.2 Separate observed facts from moral labels

A shortfall is an observed fact. “Cheating” is a classification. “Enemy” is a policy conclusion. Keep those layers separate:

```text
transfer facts -> event classifier -> sentiment update -> action features -> utility scoring
```

### 14.3 Gifts can be strategic

A gift might be genuine cooperation, reputation-building, a bribe, or manipulation. The first implementation can treat gifts positively, but later versions should track whether gifts are followed by exploitation.

### 14.4 Do not overfit fitness to one behavior

If you reward only honesty, bots may become honest but poor. If you reward only wealth, bots may become exploitative. If you reward only gifts, bots may become self-destructive. Fitness should balance survival, production, contract reliability, and social success.

## 15. A small worked example

Bot A agrees to trade with Bot B.

Promise:

```text
A sends: 2 wood
B sends: 2 food
```

Resolution:

```text
A actually sends: 2 wood
A actually receives: 1 food
```

Assume A values food and wood equally:

```text
V_A(promised_by_B) = 2
V_A(actual_received) = 1
shortfall = 1
shortfall_ratio = 1 / 2 = 0.5
```

If tolerance is 0.1, this is trade cheating.

Evidence might be:

```text
trust_e = -0.5
fairness_e = -0.5
hostility_e = 0.25
affinity_e = -0.25
generosity_e = 0
reciprocity_e = 0.5  # they owe me
```

If current trust is 0, decay is 0.02, alpha is 0.5:

```text
trust' = (1 - 0.02) * 0 + 0.5 * (-0.5)
trust' = -0.25
```

Future trades with B are discounted:

```text
reliability(A,B) = 0.5 + 0.5 * trust(A,B)
                 = 0.5 + 0.5 * (-0.25)
                 = 0.375
```

So if B promises 4 food later, A only expects:

```text
expected value = 4 * 0.375 = 1.5 food-equivalent
```

That is exactly the behavioral shift we want: the bot does not need a hardcoded grudge. It learns that B’s promises are worth less.

## 16. Recommended next code change

The best first code change is not to add new goals. It is to make resolved exchange data reliable and classifiable.

Start here:

1. Fix or extend `service/game/actions/contracts.py` so `trade_history` records the actual capped transfer boxes.
2. Add trade reason metadata to `TradeContract`.
3. Add a pure exchange classifier with tests.
4. Add `SocialMemory` and tests.
5. Feed relationship features into `ActionFeatureCalculator`.
6. Add social genome genes and scorer weights.
7. Only then consider new social goals.

This order keeps the architecture clean: facts first, memory second, scoring third, training last.

## 17. Sources and conceptual anchors

The code chapter above is grounded primarily in the repository files listed at the top.

For the general concepts, the relevant foundations are:

- Goal-Oriented Action Planning as used in game AI, especially the F.E.A.R.-style sense-plan-act architecture associated with Jeff Orkin's GOAP work.
- Classical AI planning concepts from STRIPS-like planning: world state, goals, preconditions, effects, and action search.
- Genetic algorithm fundamentals from Holland/Goldberg-style evolutionary computation: population, fitness, selection, crossover, mutation, elitism.
- Computational trust and reputation systems: directional trust, evidence updates, decay, confidence, and reputation as an accumulated belief rather than a single event label.
- Repeated-game social-dilemma design: cooperation, defection, retaliation, forgiveness, and reciprocity.

Those concepts map cleanly onto this codebase because the bot already separates objective perception, utility-weighted goals, legal action generation, action features, and genetic fitness.
