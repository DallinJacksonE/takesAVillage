import asyncio
import httpx
import os
import json
import uuid
import random
from db import db
from game_manager import create_game

# In-memory tracking of active generational loops
# Key: training_session_id -> Value: dict of training state
active_training_sessions = {}

# Genome field names mirrored from bots.models.genetic.Genome
GENOME_FIELDS = [
    "food_weight",
    "wood_weight",
    "iron_weight",
    "food_desperation_weight",
    "wood_desperation_weight",
    "iron_desperation_weight",
    "survival_weight",
    "growth_weight",
    "reputation_weight",
    "aggression_weight",
    "cooperation_weight",
    "risk_weight",
    "farm_preference",
    "woods_preference",
    "mine_preference",
    "build_weight",
    "upgrade_weight",
    "maintain_weight",
    "contest_weight",
    "work_weight",
    "fire_weight",
    "immediate_reward_weight",
    "future_reward_weight",
]


def _random_genome_dict():
    return {f: random.uniform(0, 3) for f in GENOME_FIELDS}


def _mutate_genome(genome: dict, mutation_strength=0.25, mutation_rate=0.15) -> dict:
    out = {}
    for k, v in genome.items():
        if random.random() < mutation_rate:
            out[k] = v + random.gauss(0.5, mutation_strength)
        else:
            out[k] = v
    return out


def _crossover_genomes(a: dict, b: dict) -> dict:
    out = {}
    for k in GENOME_FIELDS:
        out[k] = random.choice([a.get(k, 0), b.get(k, 0)])
    return out


async def start_training_session(ruleset: str,
                                 bot_count: int,
                                 generations: int,
                                 base_genome_id: str):
    session_id = str(uuid.uuid4())
    print(f"[Orchestrator] Starting session {session_id[:8]}")
    print(f"  - Ruleset: {ruleset}")
    print(f"  - Bot count: {bot_count}")
    print(f"  - Generations: {generations}")
    print(f"  - Base genome ID: {base_genome_id}")
    
    # Resolve the base genome from DB if it's not "random"
    base_genome_data = None
    if base_genome_id != "random":
        all_genomes = db.get_all_genomes()
        for g in all_genomes:
            if str(g['id']) == str(base_genome_id):
                base_genome_data = g['genome_data']
                print(f"[Orchestrator] Base genome {base_genome_id} successfully loaded from DB.")
                break
        if not base_genome_data:
            print(f"[Orchestrator] WARNING: Base genome {base_genome_id} not found. Falling back to random.")

    # Initialize population
    population = []
    if base_genome_data:
        population.append(base_genome_data)
        for _ in range(bot_count - 1):
            population.append(_mutate_genome(base_genome_data))
    else:
        for _ in range(bot_count):
            population.append(_random_genome_dict())

    active_training_sessions[session_id] = {
        "ruleset": ruleset,
        "bot_count": bot_count,
        "generations_left": generations,
        "population": population,
        "generation": 1,
        # genetic hyperparameters
        "elite_count": 1,
        "selection_size": min(4, bot_count),
        "mutation_strength": 0.25,
        "mutation_rate": 0.15,
    }

    print("[Orchestrator] Session built. Triggering generation 1...")
    await _trigger_next_generation(session_id)
    return session_id


async def _trigger_next_generation(session_id: str):
    session = active_training_sessions.get(session_id)
    if not session:
        return

    gen_num = session.get("generation", 1)
    ruleset = session.get("ruleset", "default")

    # 1. Create the headless game
    # 'training=True' flag bypasses the host connection requirement
    print(f"[Orchestrator] Creating game for generation {gen_num} with ruleset: {ruleset}")
    game_id = create_game(
        user_cookie="TRAINING_ORCHESTRATOR",
        ruleset=ruleset,
        bots=session["bot_count"],
        training=True,
        training_session_id=session_id
    )
    print(f"[Orchestrator] Headless game {game_id} created for generation {gen_num}! Calling Bot Service to spawn {session['bot_count']} bots...")

    # 2. Call the Bot Server to spawn bots with the current population
    bot_spawn_url = os.environ.get("BOT_SERVICE_URL", "http://bots:8001/api/spawn_bots")
    bot_secret = os.environ.get("BOT_SECRET", "default_dev_secret")

    async with httpx.AsyncClient() as client:
        try:
            await client.post(bot_spawn_url, json={
                "gameId": game_id,
                "botCount": session["bot_count"],
                "botSecret": bot_secret,
                "baseGenome": session.get("population")
            }, timeout=10.0)
            print(f"🧬 Generation {gen_num} started for session {session_id[:6]} in game {game_id}")
        except Exception as e:
            print(f"Failed to reach Bot Service: {e}")


async def handle_training_game_ended(game_id: str, training_session_id: str):
    """
    Called by the game loop when a training game finishes.
    Fetches the genomes for the completed game, performs selection/crossover/mutation
    to build the next generation population, and either triggers the next generation
    or finalizes the training loop and stores the champion.
    """
    session = active_training_sessions.get(training_session_id)
    if not session:
        return

    bot_url = os.environ.get("BOT_SERVICE_URL", "http://bots:8001")

    entries = None

    # 1. Fetch all genome entries for this game from the Bot Server
    async with httpx.AsyncClient() as client:
        try:
            await asyncio.sleep(.1)
            response = await client.get(f"{bot_url}/api/genomes/{game_id}/all", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])
                print(f"🧬 Retrieved {len(entries)} genome entries for {game_id}")
            else:
                # Fallback to single-best endpoint
                response = await client.get(f"{bot_url}/api/genomes/{game_id}", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    entries = [{
                        "game_id": game_id,
                        "fitness": data.get("best_fitness", 0),
                        "genome": data.get("genome")
                    }]
                    print(f"🧬 Fallback: retrieved single champion for {game_id}")
                else:
                    print(f"⚠️ Failed to fetch genomes for {game_id}: {response.text}")
        except Exception as e:
            print(f"❌ Failed to reach Bot Service to fetch genomes: {e}")

    best_genome = None
    if entries:
        # Sort by fitness descending
        entries_sorted = sorted(entries, key=lambda e: float(e.get("fitness", 0)), reverse=True)
        best_genome = entries_sorted[0].get("genome")
        # Build next generation
        bot_count = session["bot_count"]
        elite_count = session.get("elite_count", 1)
        selection_size = session.get("selection_size", min(4, bot_count))
        mutation_strength = session.get("mutation_strength", 0.25)
        mutation_rate = session.get("mutation_rate", 0.15)

        # Select top parents to use for crossover
        parents = [e.get("genome") for e in entries_sorted[:selection_size] if e.get("genome")]

        next_population = []
        # 1. Elitism: carry over top N unchanged
        for i in range(min(elite_count, len(parents))):
            next_population.append(parents[i])

        # 2. Fill the rest by crossover + mutation
        while len(next_population) < bot_count:
            if len(parents) >= 2:
                a, b = random.sample(parents, 2)
                child = _crossover_genomes(a, b)
            elif len(parents) == 1:
                child = dict(parents[0])
            else:
                child = _random_genome_dict()

            child = _mutate_genome(child, mutation_strength=mutation_strength, mutation_rate=mutation_rate)
            next_population.append(child)

        session["population"] = next_population

    # If we found a best genome, update the session base pointer for legacy compatibility
    if best_genome:
        session["base_genome"] = best_genome

    # Advance generation counter and decrement remaining generations
    session["generations_left"] -= 1
    session["generation"] = session.get("generation", 1) + 1

    if session["generations_left"] > 0:
        print(f"🧬 Generation complete. {session['generations_left']} remaining.")
        await _trigger_next_generation(training_session_id)
    else:
        print(f"🏆 Training Loop {training_session_id[:6]} Finished!")

        # Store the final champion in the database
        shorthand = "G" + str(uuid.uuid4())[:3].upper()
        name = f"genome_gen_{training_session_id[:6]}"

        genome_to_save = best_genome if best_genome else (session.get("population") or [None])[0]
        if genome_to_save:
            db.store_genome(name, shorthand, json.dumps(genome_to_save))
            print(f"💾 Stored final champion for session {training_session_id[:6]}")
        else:
            print(f"⚠️ No genome data available to save for session {training_session_id[:6]}")

        del active_training_sessions[training_session_id]
