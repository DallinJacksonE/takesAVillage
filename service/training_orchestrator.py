import asyncio
import httpx
import os
import json
import uuid
from datetime import datetime, timedelta
from bot_service_client import BotServiceClient
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


def _bot_service_client() -> BotServiceClient:
    return BotServiceClient(
        base_url=os.environ.get("BOT_SERVICE_URL", "http://bots:8001"),
        bot_secret=os.environ.get("BOT_SECRET", "default_dev_secret"),
        client_factory=httpx.AsyncClient,
    )


def _parse_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def _record_heartbeat(session_id: str, phase: str):
    session = active_training_sessions.get(session_id, {})
    if hasattr(db, "record_training_batch_heartbeat"):
        db.record_training_batch_heartbeat(
            session_id,
            phase,
            int(session.get("generation", 0) or 0),
            session.get("current_game_id"),
        )


async def reconcile_stalled_training_sessions(stale_after_seconds: int = 600,
                                              attempt_stale_after_seconds: int | None = None):
    cutoff = datetime.now() - timedelta(seconds=stale_after_seconds)
    if hasattr(db, "get_training_batches"):
        for batch in db.get_training_batches():
            if batch.get("status") != "running":
                continue
            batch_id = batch.get("batch_id")
            if batch_id in active_training_sessions:
                continue
            heartbeat = _parse_datetime(batch.get("last_heartbeat_at"))
            started_at = _parse_datetime(batch.get("started_at"))
            last_seen = heartbeat or started_at
            if last_seen and last_seen > cutoff:
                continue
            db.update_training_batch_status(
                batch_id,
                "stalled",
                "Training batch is running in persistence but not active in orchestrator memory.",
            )

    attempt_threshold = attempt_stale_after_seconds or stale_after_seconds
    attempt_cutoff = datetime.now() - timedelta(seconds=attempt_threshold)
    for session_id, session in list(active_training_sessions.items()):
        for game_id, attempt in list(session.get("generation_attempts", {}).items()):
            if attempt.get("status") not in ("spawning", "running"):
                continue
            last_seen = _parse_datetime(attempt.get("updated_at"))
            if last_seen and last_seen > attempt_cutoff:
                continue
            await _record_terminal_game_attempt(
                session_id,
                game_id,
                [],
                f"Training game attempt is stale in {attempt.get('status')} state.",
            )


async def training_watchdog_loop(interval_seconds: int = 30,
                                 stale_after_seconds: int = 600):
    while True:
        await reconcile_stalled_training_sessions(stale_after_seconds)
        await asyncio.sleep(interval_seconds)


async def start_training_session(ruleset: str, bot_count: int, generations: int,
                                 base_genome_id: str,
                                 bot_model: str = "genetic",
                                 mutation_strength: float = 0.25,
                                 mutation_rate: float = 0.15,
                                 random_immigrant_count: int = 1,
                                 games_per_generation: int = 5):
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
        'games_per_generation': max(1, int(games_per_generation)),
        'games_completed': 0, 'games_failed': 0,
        'current_generation_game_index': 0,
        'fitness_entries': [], 'games': [], "all_fitness_entries": [],
        "processed_game_ids": set(),
        "generation_attempts": {},
        "generation_terminal_game_ids": set(),
        "generation_scheduled": False,
        "generation_lock": asyncio.Lock(),
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
            "games_per_generation": active_training_sessions[session_id]["games_per_generation"],
        },
    })
    _record_heartbeat(session_id, "starting")

    await training_update_hub.broadcast_sessions(active_training_sessions)

    orch_logger.info("Session built. Triggering generation 1...")
    await _trigger_next_game(session_id)
    return session_id


async def cancel_training_session(session_id: str,
                                  reason: str = "Training cancelled by operator") -> bool:
    session = active_training_sessions.get(session_id)
    if session and "generation_lock" in session:
        async with session["generation_lock"]:
            active_training_sessions.pop(session_id, None)
    else:
        active_training_sessions.pop(session_id, None)
    if hasattr(db, "update_training_batch_status"):
        db.update_training_batch_status(session_id, "cancelled", reason)
    await training_update_hub.broadcast_sessions(active_training_sessions)
    return bool(session)


async def _trigger_next_game(session_id: str):
    await _start_generation_games(session_id)


async def _start_generation_games(session_id: str):
    session = active_training_sessions.get(session_id)
    if not session:
        return
    
    if session.get("generation_scheduled"):
        orch_logger.warning(f"Generation already in progress for {session_id}")
        return

    session["generation_scheduled"] = True
    session.setdefault("generation_lock", asyncio.Lock())
    session["generation_attempts"] = {}
    session["generation_terminal_game_ids"] = set()

    gen_num = session.get("generation", 1)
    ruleset = session.get("ruleset", "default")
    orch_logger.info(f"Creating {session['games_per_generation']} headless games for gen "
                     f"{gen_num} with ruleset: {ruleset}")

    tasks = []
    for attempt in range(1, session["games_per_generation"] + 1):
        tasks.append(asyncio.create_task(
            _start_generation_game_attempt(session_id, attempt)))
    await asyncio.gather(*tasks)


async def _start_generation_game_attempt(session_id: str, attempt: int):
    session = active_training_sessions.get(session_id)
    if not session:
        return

    gen_num = session.get("generation", 1)
    ruleset = session.get("ruleset", "default")
    game_id = create_game(
        user_cookie="TRAINING_ORCHESTRATOR", ruleset=ruleset,
        bots=session["bot_count"], training=True, training_session_id=session_id,
        training_generation=gen_num
    )
    session["current_game_id"] = game_id
    session["current_generation_game_index"] = attempt
    session["games"].append(game_id)
    session.setdefault("generation_attempts", {})[game_id] = {
        "attempt": attempt,
        "status": "spawning",
        "updated_at": datetime.now(),
    }
    db.mark_training_batch_game_started(session_id, game_id, gen_num, attempt)
    _record_heartbeat(session_id, "spawning")
    await training_update_hub.broadcast_sessions(active_training_sessions)

    result = await _bot_service_client().spawn_bots(
        game_id=game_id,
        bot_count=session["bot_count"],
        base_genome=session.get("population"),
        bot_model=session.get("bot_model", "genetic"),
        training_attempt_index=attempt,
    )
    if result.ok:
        db.mark_training_batch_game_running(session_id, game_id)
        session["generation_attempts"][game_id]["status"] = "running"
        session["generation_attempts"][game_id]["updated_at"] = datetime.now()
        _record_heartbeat(session_id, "running")
        orch_logger.info(f"Game {attempt}/{session['games_per_generation']} started for generation {gen_num} in game {game_id}")
        return

    orch_logger.error(f"Failed to reach Bot Service: {result.error_message}")
    await _record_terminal_game_attempt(
        session_id, game_id, [], f"Bot service spawn failed: {result.error_message}")


async def handle_training_game_ended(game_id: str, training_session_id: str):
    session = active_training_sessions.get(training_session_id)
    if not session:
        return

    async with session.setdefault("generation_lock", asyncio.Lock()):
        if game_id in session.setdefault("processed_game_ids", set()):
            orch_logger.warning(f"Duplicate game-ended ignored for {game_id}")
            return

    _record_heartbeat(training_session_id, "collecting_genomes")
    entries = await _fetch_training_game_entries(game_id)
    await _record_terminal_game_attempt(
        training_session_id,
        game_id,
        entries,
        None if entries else "No genome entries returned",
    )


async def _fetch_training_game_entries(game_id: str) -> list:
    result = await _bot_service_client().fetch_game_genomes(game_id)
    if result.ok:
        entries = result.entries or []
        orch_logger.info(f"Retrieved {len(entries)} genome entries for {game_id}")
        return entries
    orch_logger.error(
        f"Failed to reach Bot Service to fetch genomes: {result.error_message}")
    return []


async def _record_terminal_game_attempt(training_session_id: str, game_id: str,
                                        entries: list,
                                        error_message: str | None = None):
    start_next_generation = False
    session = active_training_sessions.get(training_session_id)
    if not session:
        return

    async with session.setdefault("generation_lock", asyncio.Lock()):
        processed_game_ids = session.setdefault("processed_game_ids", set())
        if game_id in processed_game_ids:
            orch_logger.warning(f"Duplicate game-ended ignored for {game_id}")
            return

        processed_game_ids.add(game_id)
        session.setdefault("generation_terminal_game_ids", set()).add(game_id)
        if game_id in session.setdefault("generation_attempts", {}):
            session["generation_attempts"][game_id]["status"] = (
                "completed" if entries else "failed")

        if entries:
            session['fitness_entries'].extend(entries)
            session["all_fitness_entries"].extend(entries)
            fitness_values = [float(entry.get("fitness", 0)) for entry in entries]
            db.mark_training_batch_game_completed(
                training_session_id,
                game_id,
                len(entries),
                {
                    "best_fitness": max(fitness_values) if fitness_values else 0.0,
                    "average_fitness": (
                        sum(fitness_values) / len(fitness_values)
                        if fitness_values else 0.0
                    ),
                },
            )
        else:
            session["games_failed"] = session.get("games_failed", 0) + 1
            if hasattr(db, "mark_training_batch_game_failed"):
                db.mark_training_batch_game_failed(
                    training_session_id, game_id,
                    error_message or "No genome entries returned")

        session["games_completed"] = len(session["generation_terminal_game_ids"])
        if session["games_completed"] < session["games_per_generation"]:
            orch_logger.info(
                f"Generation {session['generation']} "
                f"Game {session['games_completed']}/"
                f"{session['games_per_generation']} complete."
            )
            await training_update_hub.broadcast_sessions(active_training_sessions)
            return

        start_next_generation = await _complete_generation_locked(
            training_session_id, session)

    if start_next_generation:
        await _trigger_next_game(training_session_id)


async def _complete_generation_locked(training_session_id: str, session: dict) -> bool:
    entries = session["fitness_entries"]
    _record_heartbeat(training_session_id, "aggregating_generation")

    combined = {}
    for entry in entries:
        key = json.dumps(entry["genome"], sort_keys=True)
        if key not in combined:
            combined[key] = entry.copy()
            combined[key]["fitness"] = 0.0
            combined[key]["games"] = 0
        combined[key]["fitness"] += float(entry.get("fitness", 0))
        combined[key]["games"] += 1

    entries_sorted = []
    for entry in combined.values():
        entry["fitness"] /= entry["games"]
        del entry["games"]
        entries_sorted.append(entry)

    entries_sorted.sort(key=lambda e: e["fitness"], reverse=True)

    best_genome = None
    if entries_sorted:
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

        slots_available = bot_count - session.get("random_immigrant_count", 1) - 2
        crossover_child_count = slots_available // 2
        mutation_child_count = slots_available - crossover_child_count

        session["population"] = build_next_population(
            bot_model, entries_sorted, bot_count,
            elite_count=elite_count,
            selection_size=selection_size,
            mutation_strength=mutation_strength,
            mutation_rate=mutation_rate,
            random_immigrant_count=session.get("random_immigrant_count", 1),
            crossover_child_count=crossover_child_count,
            mutation_child_count=mutation_child_count
        )
        session["fitness_entries"] = []

    if best_genome:
        session["base_genome"] = best_genome

    session["games_completed"] = 0
    session["games_failed"] = 0
    session["current_generation_game_index"] = 0
    session["processed_game_ids"] = set()
    session["generation_terminal_game_ids"] = set()
    session["generation_attempts"] = {}
    session["generation_scheduled"] = False
    session["generations_left"] -= 1

    await training_update_hub.broadcast_sessions(active_training_sessions)

    if session["generations_left"] > 0:
        session["generation"] += 1
        orch_logger.info(f"Generation complete. "
                         f"{session['generations_left']} remaining.")
        return True

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

    db.complete_training_batch(training_session_id, final_champion_genome_id)
    del active_training_sessions[training_session_id]
    await training_update_hub.broadcast_sessions(active_training_sessions)
    return False