import asyncio
import httpx
import os
import json
import uuid
from db import db
from game_manager import create_game
from logger import BackendLogger
from training_genomes import (
    mutate_genome_for_model,
    normalize_genome_for_model,
    random_genome_dict_for_model,
)
from training_population import (
    build_generation_statistics,
    build_next_population,
)
from training_updates import training_update_hub

orch_logger = BackendLogger("orchestrator")
active_training_sessions = {}


async def start_training_session(ruleset: str, bot_count: int, generations: int,
                                 base_genome_id: str,
                                 bot_model: str = "genetic",
                                 mutation_strength: float = 0.25,
                                 mutation_rate: float = 0.15,
                                 random_immigrant_count: int = 1):
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
        population.append(normalize_genome_for_model(bot_model, base_genome_data))
        for _ in range(bot_count - 1):
            population.append(mutate_genome_for_model(bot_model, base_genome_data))
    else:
        for _ in range(bot_count):
            population.append(random_genome_dict_for_model(bot_model))

    # Add the bot_model to the session state
    active_training_sessions[session_id] = {
        "ruleset": ruleset, "bot_count": bot_count, "generations_left": generations,
        "population": population, "generation": 1, "elite_count": 2,
        "selection_size": min(3, bot_count), "mutation_strength": mutation_strength,
        "mutation_rate": mutation_rate, "random_immigrant_count": random_immigrant_count,
        "generation_statistics": [], "bot_model": bot_model,
        'games': []
    }
    db.create_training_batch(session_id, {
        "ruleset": ruleset,
        "bot_model": bot_model,
        "bot_count": bot_count,
        "total_generations": generations,
        "base_genome_id": base_genome_id,
        "config": {
            "mutation_strength": mutation_strength,
            "mutation_rate": mutation_rate,
            "random_immigrant_count": random_immigrant_count,
            "elite_count": active_training_sessions[session_id]["elite_count"],
            "selection_size": active_training_sessions[session_id]["selection_size"],
        },
    })

    await training_update_hub.broadcast_sessions(active_training_sessions)

    orch_logger.info("Session built. Triggering generation 1...")
    await _trigger_next_generation(session_id)
    return session_id


async def _trigger_next_generation(session_id: str):
    session = active_training_sessions.get(session_id)
    if not session:
        return
    
    if session.get("generation_in_progress"):
        orch_logger.warning(f"Generation already in progress for {session_id}")
        return

    session["generation_in_progress"] = True

    gen_num = session.get("generation", 1)
    ruleset = session.get("ruleset", "default")

    orch_logger.info(f"Creating headless game for gen "
                     f"{gen_num} with ruleset: {ruleset}")
    game_id = create_game(
        user_cookie="TRAINING_ORCHESTRATOR", ruleset=ruleset,
        bots=session["bot_count"], training=True, training_session_id=session_id,
        training_generation=gen_num
    )
    active_training_sessions[session_id]["current_game_id"] = game_id
    db.mark_training_batch_game_started(session_id, game_id, gen_num)
    await training_update_hub.broadcast_sessions(active_training_sessions)

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
    session["generation_in_progress"] = False


async def handle_training_game_ended(game_id: str, training_session_id: str):
    session = active_training_sessions.get(training_session_id)
    if not session:
        return
    
    if session.get("generation_in_progress"):
        orch_logger.warning("Duplicate game-ended ignored")
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
        bot_model = session.get("bot_model", "genetic")
        best_genome = normalize_genome_for_model(
            bot_model, entries_sorted[0].get("genome"))
        bot_count = session["bot_count"]
        elite_count = session.get("elite_count", 1)
        selection_size = session.get("selection_size", min(4, bot_count))
        mutation_strength = session.get("mutation_strength", 0.25)
        mutation_rate = session.get("mutation_rate", 0.15)

        generation_stats = build_generation_statistics(entries_sorted)
        session.setdefault("generation_statistics", []).append({
            "generation": session.get("generation", 1),
            **generation_stats,
        })
        db.append_training_batch_generation_stats(
            training_session_id,
            {"generation": session.get("generation", 1), **generation_stats})
        orch_logger.info(f"Generation stats: {generation_stats}")
        session["population"] = build_next_population(
            bot_model, entries_sorted, bot_count,
            elite_count=elite_count,
            selection_size=selection_size,
            mutation_strength=mutation_strength,
            mutation_rate=mutation_rate,
            random_immigrant_count=session.get("random_immigrant_count", 1),
        )

    if best_genome:
        session["base_genome"] = best_genome

    session["generations_left"] -= 1
    session["generation"] += 1
    await training_update_hub.broadcast_sessions(active_training_sessions)

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
        final_champion_genome_id = None
        if genome_to_save:
            db.store_genome(name, shorthand, json.dumps(genome_to_save))
            final_champion_genome_id = name
            orch_logger.info(f"Stored final champion for session "
                             f"{training_session_id[:6]}")
        else:
            orch_logger.warning(f"No genome data available to save for "
                                f"session {training_session_id[:6]}")
            
        game_stats = {
            "game_id": game_id,
            "trade_count": sum(
                len(e.get("events", {}).get("trades", []))
                for e in entries
            ),
            "contest_count": sum(
                len(e.get("events", {}).get("contests", []))
                for e in entries
            ),
        }

        session.setdefault("games", {})

        session["games"][game_id] = {
            "game_id": game_id,
            "trade_count": game_stats["trade_count"],
            "contest_count": game_stats["contest_count"],
        }

        db.complete_training_batch(training_session_id, final_champion_genome_id)
        del active_training_sessions[training_session_id]
        await training_update_hub.broadcast_sessions(active_training_sessions)