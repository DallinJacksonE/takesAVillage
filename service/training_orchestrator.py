import asyncio
import httpx
import os
import json
import uuid
import random
from db import db
from game_manager import create_game
from logger import BackendLogger

orch_logger = BackendLogger("orchestrator")
active_training_sessions = {}

GENOME_FIELDS = [
    "food_weight", "wood_weight", "iron_weight", "food_desperation_weight",
    "wood_desperation_weight", "iron_desperation_weight", "survival_weight",
    "growth_weight", "reputation_weight", "aggression_weight", "cooperation_weight",
    "risk_weight", "farm_preference", "woods_preference", "mine_preference",
    "build_weight", "upgrade_weight", "maintain_weight", "contest_weight",
    "work_weight", "fire_weight", "immediate_reward_weight", "future_reward_weight",
]


def _random_genome_dict():
    return {f: random.uniform(0, 3) for f in GENOME_FIELDS}


def _mutate_genome(genome: dict, mutation_strength=0.25, mutation_rate=0.15) -> dict:
    out = {}
    for k, v in genome.items():
        if random.random() < mutation_rate:
            out[k] = v + random.gauss(0, mutation_strength)
        else:
            out[k] = v
    return out


def _crossover_genomes(a: dict, b: dict) -> dict:
    out = {}
    for k in GENOME_FIELDS:
        out[k] = random.choice([a.get(k, 0), b.get(k, 0)])
    return out


async def start_training_session(ruleset: str, bot_count: int, generations: int, base_genome_id: str, bot_model: str = "genetic"):
    session_id = str(uuid.uuid4())
    orch_logger.info(f"Starting session {session_id[:8]} | "
                     f"Ruleset: {ruleset} | "
                     f"Bots: {bot_count} | Gens: {generations} | "
                     f"Base: {base_genome_id} | Model: {bot_model}")

    base_genome_data = None
    if base_genome_id != "random":
        all_genomes = db.get_all_genomes()
        for g in all_genomes:
            if str(g['id']) == str(base_genome_id):
                base_genome_data = g['genome_data']
                orch_logger.info(
                    f"Base genome {base_genome_id} successfully loaded from DB.")
                break
        if not base_genome_data:
            orch_logger.warning(
                f"Base genome {base_genome_id} not found. Falling back to random.")

    population = []
    if base_genome_data:
        population.append(base_genome_data)
        for _ in range(bot_count - 1):
            population.append(_mutate_genome(base_genome_data))
    else:
        for _ in range(bot_count):
            population.append(_random_genome_dict())

    # Add the bot_model to the session state
    active_training_sessions[session_id] = {
        "ruleset": ruleset, "bot_count": bot_count, "generations_left": generations-1,
        "population": population, "generation": 1, "elite_count": 2,
        "selection_size": min(3, bot_count), "mutation_strength": 0.25, "mutation_rate": 0.15,
        "bot_model": bot_model
    }

    orch_logger.info("Session built. Triggering generation 1...")
    await _trigger_next_generation(session_id)
    return session_id


async def _trigger_next_generation(session_id: str):
    session = active_training_sessions.get(session_id)
    if not session:
        return

    gen_num = session.get("generation", 1)
    ruleset = session.get("ruleset", "default")

    orch_logger.info(f"Creating headless game for gen "
                     f"{gen_num} with ruleset: {ruleset}")
    game_id = create_game(
        user_cookie="TRAINING_ORCHESTRATOR", ruleset=ruleset,
        bots=session["bot_count"], training=True, training_session_id=session_id
    )
    active_training_sessions[session_id]["current_game_id"] = game_id

    bot_spawn_url = os.environ.get(
        "BOT_SERVICE_URL", "http://bots:8001")
    bot_secret = os.environ.get("BOT_SECRET", "default_dev_secret")

    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{bot_spawn_url}/api/spawn_bots", json={
                "gameId": game_id,
                "botCount": session["bot_count"],
                "botSecret": bot_secret,
                "baseGenome": session.get("population"),
                # <-- Pass to Bot Server
                "botModel": session.get("bot_model", "genetic")
            }, timeout=10.0)
            orch_logger.info(f"Generation {gen_num} started for session "
                             f"{session_id[:6]} in game {game_id}")
        except Exception as e:
            orch_logger.error("Failed to reach Bot Service", exc=e)


async def handle_training_game_ended(game_id: str, training_session_id: str):
    session = active_training_sessions.get(training_session_id)
    if not session:
        return

    bot_url = os.environ.get("BOT_SERVICE_URL", "http://bots:8001")
    entries = None

    async with httpx.AsyncClient() as client:
        try:
            await asyncio.sleep(.1)
            response = await client.get(f"{bot_url}/api/genomes/{game_id}/all", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])
                orch_logger.info(
                    f"Retrieved {len(entries)} genome entries for {game_id}")
            else:
                response = await client.get(f"{bot_url}/api/genomes/{game_id}", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    entries = [{"game_id": game_id, "fitness": data.get(
                        "best_fitness", 0), "genome": data.get("genome")}]
                    orch_logger.info(
                        f"Fallback: retrieved single champion for {game_id}")
                else:
                    orch_logger.error(f"Failed to fetch genomes for "
                                      f"{game_id}: {response.text}")
        except Exception as e:
            orch_logger.error(
                "Failed to reach Bot Service to fetch genomes", exc=e)

    best_genome = None
    if entries:
        entries_sorted = sorted(entries, key=lambda e: float(
            e.get("fitness", 0)), reverse=True)
        best_genome = entries_sorted[0].get("genome")
        bot_count = session["bot_count"]
        elite_count = session.get("elite_count", 1)
        selection_size = session.get("selection_size", min(4, bot_count))
        mutation_strength = session.get("mutation_strength", 0.25)
        mutation_rate = session.get("mutation_rate", 0.15)

        parents = [e.get("genome")
                   for e in entries_sorted[:selection_size] if e.get("genome")]
        next_population = []
        for i in range(min(elite_count, len(parents))):
            next_population.append(parents[i])

        while len(next_population) < bot_count:
            if len(parents) >= 2:
                a, b = random.sample(parents, 2)
                child = _crossover_genomes(a or {}, b or {})
            elif len(parents) == 1:
                child = dict(parents[0] or {})
            else:
                child = _random_genome_dict()
            child = _mutate_genome(
                child, mutation_strength=mutation_strength, mutation_rate=mutation_rate)
            next_population.append(child)

        session["population"] = next_population

    if best_genome:
        session["base_genome"] = best_genome

    session["generations_left"] -= 1
    session["generation"] = session.get("generation", 1) + 1

    if session["generations_left"] > 0:
        orch_logger.info(f"Generation complete. "
                         f"{session['generations_left']} remaining.")
        await _trigger_next_generation(training_session_id)
    else:
        orch_logger.info(f"Training Loop {training_session_id[:6]} Finished!")
        shorthand = "G" + str(uuid.uuid4())[:3].upper()
        name = f"genome_gen_{training_session_id[:6]}"

        genome_to_save = best_genome if best_genome else (
            session.get("population") or [None])[0]
        if genome_to_save:
            db.store_genome(name, shorthand, json.dumps(genome_to_save))
            orch_logger.info(f"Stored final champion for session "
                             f"{training_session_id[:6]}")
        else:
            orch_logger.warning(f"No genome data available to save for "
                                f"session {training_session_id[:6]}")

        del active_training_sessions[training_session_id]
