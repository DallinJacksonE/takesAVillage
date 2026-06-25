# GOAP Genetic Bot Improvement Checklist

Goal: make `bots/models/goap_genetic/` a strong GOAP bot architecture for Takes a Village while keeping behavior learnable from genomes instead of fixed tactical constants.

Implementation boundary: this is a planning/checklist document only. Before implementing code beyond small scaffolding, review the open questions with dj.

Current implementation decisions from dj:
- Prioritize each bot's own survival for now; social dynamics can come later.
- Deception should be learnable behavior.
- Do not penalize undercutting trades/wages in current fitness.
- Keep `GeneticBot` untouched.
- Use a new GOAP-specific genome when GOAP needs extra genes.
- Initial benchmark: bots consistently survive longer games.

---

## Research notes that should shape the design

- Jeff Orkin describes GOAP as a simplified STRIPS-like planning architecture for real-time autonomous game character behavior, originally used for F.E.A.R. The key lesson for this bot is: actions should expose preconditions/effects, goals should be explicit world-state desires, and the planner should compose actions instead of routing goals through hand-written branches.
- Orkin's GOAP resource page also points to "3 States and a Plan: The AI of F.E.A.R." and "Agent Architecture Considerations for Real-Time Planning in Games". The practical takeaway is to keep perception, decision selection, planning, and execution separated so the bot can re-plan when the world changes.
- DEAP's evolutionary algorithm docs emphasize that crossover, mutation, selection, evaluation, statistics, and hall-of-fame behavior are separate operators, and that custom algorithms are expected when the domain requires it. For this project, the training loop should be treated as domain code, not as an opaque one-size-fits-all GA.
- Sutton & Barto's reinforcement-learning framing is useful even if we keep a genetic algorithm: define measurable state, action, reward/fitness, and policy behavior. If the genome is a policy parameterization, fitness must reflect the behavior we actually want to evolve.
- NEAT-style research is a reminder that evolving structure can matter, not just weights. We do not need NEAT now, but we should leave room for genomes to learn goal/action-feature weights and utility-curve shapes instead of only scalar action biases.

Sources checked:
- Jeff Orkin, "Goal-Oriented Action Planning (GOAP)" mirror of original MIT Media Lab page: https://static.hlt.bme.hu/semantics/external/pages/GOAP/alumni.media.mit.edu/_jorkin/goap.html
- DEAP documentation, "Operators and Algorithms": https://deap.readthedocs.io/en/master/tutorials/basic/part2.html
- DEAP documentation, "Algorithms": https://deap.readthedocs.io/en/master/api/algo.html
- Sutton & Barto, "Reinforcement Learning: An Introduction", 2nd ed.: http://incompleteideas.net/book/the-book-2nd.html
- Stanley & Miikkulainen, "Evolving Neural Networks through Augmenting Topologies": https://nn.cs.utexas.edu/downloads/papers/stanley.ec02.pdf

---

## Current repo observations

- `GOAPGenetic.choose_action()` already has the right high-level rhythm: guardrails -> `Perception.sense()` -> `Thinker.evaluate_goals()` -> `Actuator.act()` -> `format_network_payload()`.
- `Perception.sense()` is intentionally factual, but it currently omits important game facts the planner needs: rule constants, day/game length, player list summaries, map tiles, development costs, campfire cost, fire status, current contracts by type, maintenance/upgrade costs, and action history/timeline signals.
- `Thinker` currently uses genome weights, but still has fixed constants such as inverse-resource scale, tie bonus, sickness multiplier, minimum risk aversion, doubled work boost, pending-contract multiplier, and direct resource sums. These constants will dominate learning unless moved into rule facts, derived normalization, or genome genes.
- `Actuator` is a router with a hard-coded `if/elif` goal map. That is useful as temporary scaffolding, but it is not GOAP planning yet.
- `ActionGenerator` has several command mismatches with `BaseBot.get_available_actions()`:
  - Looks for `CAMPFIRE`, but legal action is `START_FIRE` for starting a fire and `CAMPFIRE` for inviting/requesting.
  - Looks for `BUILD`, `CONTEST`, `UPGRADE`, but legal actions are `BUILD_DEV`, `CONTEST_DEV`, `UPGRADE_DEV`.
  - It returns first matching actions instead of scoring all candidate bindings.
- `GeneticBot.score_action()` has more tactical domain knowledge than `goap_genetic`, including employment, build, upgrade, maintain, contest, campfire, work, trade, and finalize scoring. GOAP should reuse the available domain insight without copying the large if/elif scoring block.
- `BaseBot.get_available_actions()` is currently the source of legal actions. The GOAP layer should not invent action payloads until it can prove they match legal server payloads.
- The training loop already supports populations, elitism, crossover, mutation, and per-bot fitness, but mutation settings and selection settings are still fixed orchestrator constants.
- `calculate_fitness()` only rewards resources, survival, and days survived. It does not yet reward village-specific outcomes such as developments owned/maintained, production capacity, trade quality, cooperative survival, honoring contracts, or social leverage.

---

## Design principles for this directory

- [ ] Keep the three phases explicit:
  - perception = factual normalization only
  - thinking = choose desired goal/world state using genome-shaped utilities
  - acting = plan and execute the next legal action
- [ ] Do not encode strategic thresholds as literals in bot logic. If a number affects preference, urgency, risk, tie-breaking, planning cost, trade fairness, or tactical choice, it should be one of:
  - a genome gene
  - a value from `game_state` / ruleset constants
  - a value derived from legal action payloads or observable world state
  - a named mathematical neutral value required for safety, such as zero or one for identity/empty cases
- [ ] Treat action command names and payload keys as domain schema, not learned preferences. These can be constants/enums, but preference among them should come from the genome/planner.
- [ ] Prefer composable scorer/feature objects over long `if/elif` chains.
- [ ] Make every planner decision explainable for debugging: chosen goal, candidate action scores, rejected candidates, selected plan, and which genome genes contributed.
- [ ] Keep bot legality separate from bot preference. Legal actions come from `BaseBot.get_available_actions()` or equivalent server-derived contracts; GOAP only ranks/plans among legal actions.

---

## Phase 1: Fix the GOAP vocabulary and action schema

- [x] Create a small internal command vocabulary module, likely `bots/models/goap_genetic/domain.py`, that maps server action commands exactly:
  - `BUILD_DEV`
  - `MAINTAIN_DEV`
  - `UPGRADE_DEV`
  - `CONTEST_DEV`
  - `START_FIRE`
  - `CAMPFIRE`
  - `EMPLOYMENT`
  - `COMMIT_WORK`
  - `TRADE`
  - `ACCEPT`
  - `DENY`
  - `FINALIZE`
  - `FINISH_PHASE`
- [x] Replace command string mismatches in `ActionGenerator` before evaluating strategy quality.
- [x] Add tests for `ActionGenerator` or its replacement proving each goal can find the right command name from a representative legal action list.
- [x] Confirm whether `CAMPFIRE` should mean invite/request only and `START_FIRE` should mean creating a host fire. Capture that in code comments/tests.
- [x] Ensure GOAP never returns raw actions with helper payload keys that bypass `format_network_payload()` cleanup.

---

## Phase 2: Make perception complete but non-judgmental

- [x] Introduce a typed memory object, e.g. dataclasses in `bots/models/goap_genetic/memory.py`, so planning code stops depending on loose dict keys.
- [x] Include raw factual state:
  - [x] phase, day, game length if present, time remaining
  - [x] my id, health, sickness chance, finished phase, fire status, fire guests
  - [x] resources
  - [x] player summaries: alive/dead, resources if visible, fire status, development counts
  - [x] map tiles and tile types
  - [x] developments grouped by ownership, type, level, worker, contested status, maintenance days
  - [x] current actions/contracts grouped by type/status/waiting_on_id
  - [x] available work
  - [x] rule facts from game state: `development_costs`, `campfire_cost`, `max_fire_seats`, sickness/recovery rates
- [x] Include legal actions as perceived facts, or pass them alongside memory in a typed `DecisionContext`.
- [x] Compute derived factual features only when they are objective, for example:
  - [x] resource totals
  - [x] affordable build/upgrade/maintenance costs from rules
  - [x] resource production type for each development
  - [x] candidate trade inventories available to send
  - [x] contested developments requiring support
- [x] Do not compute "urgency", "desire", "good", "bad", or any preference-laden metric inside perception unless the curve parameters come from genome.

---

## Phase 3: Replace goal routing with real GOAP planning

- [x] Define explicit goals as desired world-state predicates, not only strings:
  - [x] stay alive / reduce sickness risk
  - [x] secure food
  - [x] secure wood / warmth
  - [x] increase production capacity
  - [x] preserve owned developments
  - [x] improve/upgrade owned developments
  - [x] secure income through work
  - [x] resolve obligations/contracts
  - [x] trade toward scarce resources
  - [x] contest valuable developments
  - [x] cooperate around campfires/contracts
- [x] Give each goal:
  - [x] a name
  - [x] a genome-weighted utility function
  - [x] a desired state predicate
  - [x] a completion evaluator
  - [x] optional phase restrictions derived from legal actions, not hard-coded tactical preference
- [x] Define GOAP actions as action templates over legal server actions:
  - [x] preconditions: facts required before action can help
  - [x] effects: predicted factual deltas
  - [x] cost function: genome-weighted opportunity/risk cost
  - [x] binding function: converts one legal action payload into a planning action instance
- [x] Build candidate action instances from `BaseBot.get_available_actions(game_state)` rather than constructing illegal actions.
- [x] Implement a simple planner first:
  - [x] score each candidate by expected progress toward the selected goal
  - [x] include action cost and predicted effects
  - [x] select next action from the best plan
- [x] Only add multi-step search after one-step effect planning is correct. Multi-step plans may be shallow because the game phases and legal actions already constrain the action space.
- [x] Re-plan every `choose_action()` call from current memory instead of persisting stale plans across phase changes.

---

## Phase 4: Make genome the source of preferences

- [x] Audit every numeric preference in `thinking.py`, `acting.py`, and `action_generator.py`.
- [x] Move preference constants into genes or genome-controlled curves. Candidates:
  - [x] resource urgency curve shape per resource
  - [x] survival urgency multiplier
  - [x] health/sickness risk aversion curve
  - [x] maintenance urgency curve as days remaining decreases
  - [x] production future-value discount
  - [x] trade fairness/greed tolerance
  - [x] employment wage preference
  - [x] employer exploitation tolerance
  - [x] campfire host/request/accept preference
  - [x] contest aggression vs defense preference
  - [x] finalize-contract honesty/compliance preference
  - [x] exploration/noise/tie-breaking amount
- [x] Consider grouping genes into small dataclasses or namespaces so the genome stays understandable as it grows:
  - [x] resource valuation genes
  - [x] curve shape genes
  - [x] goal utility genes
  - [x] action cost genes
  - [x] social/trust genes
  - [ ] evolutionary meta-genes, if we choose to evolve mutation behavior later
- [x] Clamp or transform genes in a consistent way so mutation cannot create pathological unbounded values that swamp all other signals.
- [x] Avoid negative side effects from arbitrary mutation by using normalized feature values and bounded gene transforms.
- [x] Keep neutral defaults available only for missing/backward-compatible genome fields; do not bake strategic behavior into defaults.

---

## Phase 5: Improve action evaluation without hard-coding strategy

- [x] Extract reusable action feature calculators from `GeneticBot.score_action()` into small functions/classes rather than copying its `if/elif` tree.
- [x] Features should be factual and normalized, for example:
  - [x] resource delta if action succeeds
  - [x] production delta over expected remaining days
  - [x] resource cost from ruleset
  - [x] maintenance days saved
  - [x] sickness/fire risk delta from rule rates
  - [x] trade received value and given value
  - [x] contract obligation state
  - [x] contested value at stake
  - [x] social exposure: helps self, helps other, harms other
- [x] Preference over those features should be a dot product or small utility curve controlled by genome weights.
- [x] Score all legal bindings of an action type, not just the first matching command.
- [x] For each chosen action, log or return a debug explanation showing top features and weights.
- [x] Make fallback behavior genome-compatible. If the selected goal has no legal plan, choose the next-best goal/action by utility, not always `SECURE_INCOME`.

---

## Phase 6: Make fitness align with village success

- [x] Revisit `bots/models/genetic/fitness.py` before judging GOAP quality.
- [x] Decide what "works very well" means. Possible fitness components:
  - [x] survival to game end / later days survived
  - [x] final resources
  - [x] developments owned
  - [x] total development levels
  - [x] maintained developments / avoided decay
  - [x] production generated by owned developments
  - [x] successful work commitments
  - [x] profitable trades
  - [x] fulfilled contracts/finalized promised items
  - [x] campfire survival/cooperation outcomes
  - [x] contest wins or successful defense
  - [x] relative ranking among bots, not just absolute score
- [x] Prefer multi-objective or staged fitness over a single brittle scalar if goals conflict.
- [x] Include penalties for illegal/no-op/repeatedly-finished behavior if observable in training logs.
- [x] Store enough per-bot episode statistics to explain why a genome won.
- [ ] Compare champion fitness against a fixed baseline bot and previous champion, not only the same generation.

---

## Phase 7: Strengthen the evolutionary loop

- [x] Consolidate genome field definitions so `Genome`, `training_orchestrator.GENOME_FIELDS`, serializers, and saved genomes cannot drift. (GOAP training fields live in service-owned training schema code so the training orchestrator does not import bot modules.)
- [x] Add backward-compatible genome loading for new fields.
- [x] Record generation statistics:
  - [x] best/median/worst fitness
  - [x] diversity across genes
  - [x] survival rate
  - [x] average resources/development counts
  - [x] illegal action count if available
- [x] Keep elites, but preserve diversity so all bots do not converge to one exploit too early.
- [ ] Consider tournament selection or rank-based selection if raw fitness becomes noisy.
- [ ] Consider separate evaluation matches against fixed reference populations to reduce overfitting to the current generation.
- [ ] Run multiple seeds per champion before saving if games have high randomness.
- [x] Make mutation rate/strength configurable through training session settings; optionally evolve meta-genes later.

---

## Phase 8: Testing and validation checklist

- [x] Unit tests for `Perception.sense()` with representative WORK, TRADE, and NIGHT states.
- [x] Unit tests for command vocabulary against `BaseBot.get_available_actions()` outputs.
- [x] Unit tests for every action template:
  - [x] can bind from legal action payload
  - [x] rejects mismatched payloads
  - [x] computes factual effects without strategic constants
  - [x] emits legal server payload after formatting
- [x] Unit tests for thinker utility using synthetic genomes to prove genes change goal rankings.
- [x] Regression test for the current command mismatch bugs.
- [ ] Simulation smoke test: one GOAP bot can play a full game without exceptions.
- [ ] Training smoke test: small population and two generations records all genomes and fitness values.
- [ ] Baseline comparison: GOAPGenetic vs existing `GeneticBot` across repeated games using the same seeds if possible.
- [x] Inspect logs/code paths for repeated no-op loops, always-finish behavior, contract spam, trade spam, or one action dominating all phases.

---

## Suggested implementation order

1. Fix command vocabulary and add tests for legal action matching.
2. Type and enrich perception while keeping it judgment-free.
3. Create action feature calculators from existing `GeneticBot` tactical knowledge.
4. Replace `ActionGenerator` first-match methods with candidate scoring over all legal actions.
5. Replace `Actuator` goal `if/elif` routing with a registry of goal strategies/action templates.
6. Move hard-coded preference constants from `Thinker` into genome-controlled utility curves.
7. Improve fitness and training instrumentation before running long training jobs.
8. Run short deterministic smoke tests, then compare against `GeneticBot`.
9. Only after these pass, consider deeper multi-step planning/search.

---

## Open questions for dj before implementation

- [ ] Should these bots optimize selfish victory, village-wide survival, or a mix of social and material success?
- [ ] Should deception be learnable behavior, explicitly disallowed, or fitness-dependent?
- [ ] Are bots allowed to exploit underpayment/finalize mechanics, or should fitness penalize dishonoring contracts?
- [ ] Should genome values be constrained to non-negative weights, or should negative preferences be legal?
- [ ] Do we want a compact genome for interpretability or a larger genome that can learn more curve shapes?
- [ ] Should we preserve `GeneticBot` as a baseline untouched while rebuilding GOAPGenetic, or extract shared scoring primitives into a common module?
- [ ] What is the first target benchmark: survive full game, beat current genetic bot, richer average resources, or more human-like village behavior?
