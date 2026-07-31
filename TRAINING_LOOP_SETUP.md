# Training Loop Setup - Ready to Use

The full training pipeline is now operational from the Research view. Here's how it works end-to-end:

## User Flow (Frontend)

1. **Navigate to Research Dashboard** (Research tab in the app)
2. **Click "Start Training Loop"** button (purple button in the top-right)
3. **Configure Training Session:**
   - Select a **Ruleset** (default, wealthy, custom, etc.)
   - Set **Bots per Game** (e.g., 5-10 bots)
   - Set **Generations** (how many generations to evolve)
   - Choose **Base Genome** (Random = fresh pool, or pick a saved genome from previous runs)
4. **Click "Start Training"** → Modal closes and training begins!

## System Architecture

```
Research View (Frontend)
    ↓ POST /api/research/train
Service API (/api/research/train)
    ↓ asyncio.create_task()
Training Orchestrator
    ├─ Generate initial population (seed or mutate base genome)
    ├─ Create headless game via create_game()
    ├─ POST /api/spawn_bots with full population list
    │
    Bot Service (runs bots with assigned genomes)
    ├─ Each bot plays the game
    ├─ Calculates fitness on death
    ├─ Writes genome + fitness to bot_training_data.jsonl
    │
    Game ends → Orchestrator callback:
    ├─ GET /api/genomes/{game_id}/all (fetch all genomes + fitness)
    ├─ Selection + Crossover + Mutation → Build next population
    ├─ Trigger next generation OR finish training
    │
    Final Champion
    └─ Stored in DB via db.store_genome()
```

## Key Components Modified

### Backend
- **[service/research/training/orchestrator.py](service/research/training/orchestrator.py)**
  - `_random_genome_dict()` - Create random genome
  - `_mutate_genome()` - Gaussian mutation
  - `_crossover_genomes()` - Two-point crossover
  - `start_training_session()` - Initialize population, track session
  - `handle_training_game_ended()` - Implement genetic algorithm loop
  - Full population-based evolution (not just single champion)

- **[service/api/routers/research_training.py](service/api/routers/research_training.py)**
  - `/api/research/train` - POST endpoint to start training

- **[bots/api.py](bots/api.py)**
  - `/api/genomes/{game_id}/all` - New endpoint to fetch all genomes for a game
  - Modified spawn to accept list of genomes

- **[bots/bot_multiprocessing.py](bots/bot_multiprocessing.py)**
  - Now accepts full population list instead of just base genome

### Frontend
- **[frontend/src/views/Research.tsx](frontend/src/views/Research.tsx)**
  - `handleOpenTrainingMenu()` - Fetch rulesets and genomes
  - `handleStartTraining()` - POST to /api/research/train

- **[frontend/src/components/NewGameModal.tsx](frontend/src/components/NewGameModal.tsx)**
  - Already supports `isTrainingMode` flag
  - Displays generations input, base genome selector

## Genetic Algorithm Details

### Generation Lifecycle
1. **Population Initialization** (Gen 1)
   - If `baseGenome` provided: keep 1 exact + mutate N-1 variants
   - If random: generate N random genomes

2. **Game Execution**
   - Each bot gets assigned one genome from population
   - Bots play a complete game

3. **Fitness Evaluation**
   - `calculate_fitness()` scores based on: resources, days survived, health
   - All N genomes' fitness recorded

4. **Selection & Reproduction** (Gen N+1)
   - Sort by fitness descending
   - Elitism: Keep top 1 exact
   - Roulette Selection: Pick parents weighted by fitness
   - Crossover: Combine two parents' genes
   - Mutation: Gaussian perturbation (mutation_rate=0.15, mutation_strength=0.25)
   - Repeat until population size = N

5. **Repeat** until generations_left = 0

### Genome Structure (23 genes)
```python
{
  "food_weight": 0.5,           # How much bot values food
  "wood_weight": 1.2,            # How much bot values wood
  "iron_weight": 0.8,            # How much bot values iron
  "food_desperation_weight": 1.0,
  "wood_desperation_weight": 0.9,
  "iron_desperation_weight": 0.7,
  "survival_weight": 2.0,        # Importance of staying alive
  "growth_weight": 1.5,          # Importance of expansion
  "reputation_weight": 0.3,      # Importance of social standing
  "aggression_weight": 0.2,      # Tendency to contest
  "cooperation_weight": 0.5,     # Tendency to trade/help
  "risk_weight": 0.1,            # Risk tolerance
  "farm_preference": 1.0,        # Preference for farm developments
  "woods_preference": 0.9,
  "mine_preference": 0.8,
  "build_weight": 1.5,           # Weight for building actions
  "upgrade_weight": 1.0,         # Weight for upgrades
  "maintain_weight": 0.5,        # Weight for maintenance
  "contest_weight": 0.2,         # Weight for conflicts
  "work_weight": 2.0,            # Weight for taking jobs
  "fire_weight": 0.3,            # Weight for campfire actions
  "immediate_reward_weight": 1.0,
  "future_reward_weight": 0.5
}
```

## Example Training Session

```
User: Ruleset=default, Bots=8, Generations=10, BaseGenome="random"

[Orchestrator] Starting session 9c4f... | Resolving base genome...
[Orchestrator] Session built. Triggering generation 1...
🧬 Generation 1 started for session 9c4f in game g_k2m1

// ... game plays for ~5-10 minutes ...

[game_loop] Game g_k2m1 ended
🧬 Retrieved 8 genome entries for g_k2m1
🧬 Generation complete. 9 remaining.
🧬 Generation 2 started for session 9c4f in game g_a9x3

// ... repeats ...

🏆 Training Loop 9c4f Finished!
💾 Stored final champion for session 9c4f as "genome_gen_9c4f"
```

## Monitoring

### Live Logs
- Docker: `docker logs -f takesavillage_service_1`
- Bots: `docker logs -f takesavillage_bots_1`

### View Results
- Research Dashboard → Game Logs tab shows all training games
- Click "Analyze" to see each bot's resources and actions by day

### Saved Champions
- Research Dashboard → (backend fetches from `/api/research/genomes`)
- Use saved genomes as base for next training runs

## Troubleshooting

### Training doesn't start
- Check service logs for "Received request for training loop"
- Verify `/api/research/train` endpoint is hit
- Ensure bot service is running (`docker logs takesavillage_bots_1`)

### No genomes returned in modal
- Run one complete training session first to generate champions
- Check `/api/research/genomes` returns a list
- Verify DB is persisting genomes

### Bots crash during game
- Check bot logs for errors
- Verify `GeneticBot` can handle all 23 genome fields
- Ensure `bot_training_data.jsonl` has write permissions

## Next Steps

- **Tune hyperparameters**: Adjust mutation rate and strength through `TrainingConfig` in [service/research/training/service.py](service/research/training/service.py).
- **Enhance fitness**: Modify `calculate_fitness()` in [bots/models/genetic/fitness.py](bots/models/genetic/fitness.py)
- **Parallel training**: Run multiple training sessions (each gets unique session_id)
- **Visualization**: Add graphs in Research Dashboard showing fitness over generations
