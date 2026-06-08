import asyncio
import httpx
import os
import json
import uuid
from db import db
from game_manager import create_game

# In-memory tracking of active generational loops
# Key: training_session_id -> Value: dict of training state
active_training_sessions = {}


async def start_training_session(ruleset: str,
                                 bot_count: int,
                                 generations: int,
                                 base_genome_id: str):
    session_id = str(uuid.uuid4())
    print(f"[Orchestrator] Starting session"
          f"{session_id[:8]} | Resolving base genome...")
    # Resolve the base genome from DB if it's not "random"
    base_genome_data = None
    if base_genome_id != "random":
        all_genomes = db.get_all_genomes()
        for g in all_genomes:
            if str(g['id']) == str(base_genome_id):
                base_genome_data = g['genome_data']
                print(f"Orchestrator] Base genome "
                      f"{base_genome_id} successfully loaded from DB.")
                break
        if not base_genome_data:
            print(f"Orchestrator] WARNING: Base genome "
                  f"{base_genome_id} not found. Falling back to random.")
    active_training_sessions[session_id] = {
        "ruleset": ruleset,
        "bot_count": bot_count,
        "generations_left": generations,
        "base_genome": base_genome_data
    }
    print("[Orchestrator] Session built. Triggering generation 1...")
    await _trigger_next_generation(session_id)
    return session_id


async def _trigger_next_generation(session_id: str):
    session = active_training_sessions.get(session_id)
    if not session:
        return

    # 1. Create the headless game
    # 'training=True' flag bypasses the host connection requirement
    game_id = create_game(
        user_cookie="TRAINING_ORCHESTRATOR",
        ruleset=session["ruleset"],
        bots=session["bot_count"],
        training=True,
        training_session_id=session_id
    )
    print(f"Orchestrator] Headless game"
          f"{game_id} created! Calling Bot Service to spawn "
          f"{session['bot_count']} bots...")
    # 2. Call the Bot Server to spawn bots with the current base_genome
    bot_url = os.environ.get(
        "BOT_SERVICE_URL", "http://bots:8001/api/spawn_bots")
    bot_secret = os.environ.get("BOT_SECRET", "default_dev_secret")

    async with httpx.AsyncClient() as client:
        try:
            await client.post(bot_url, json={
                "gameId": game_id,
                "botCount": session["bot_count"],
                "botSecret": bot_secret,
                "baseGenome": session["base_genome"]
            }, timeout=10.0)
            print(f"🧬 Generation started for session"
                  f" {session_id[:6]} in game {game_id}")
        except Exception as e:
            print(f"Failed to reach Bot Service: {e}")


async def handle_training_game_ended(game_id: str, training_session_id: str):
    """
    Called by the game loop when a training game finishes.
    Fetches the best genome, updates the session, and 
    triggers the next generation.
    """
    session = active_training_sessions.get(training_session_id)
    if not session:
        return

    bot_url = os.environ.get("BOT_SERVICE_URL", "http://bots:8001")
    best_genome_data = None

    # 1. Fetch the winning genome from the Bot Server
    async with httpx.AsyncClient() as client:
        try:
            await asyncio.sleep(1)

            response = await client.get(
                f"{bot_url}/api/genomes/{game_id}", timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                best_genome_data = data.get("genome")
                print(
                    f"🧬 Retrieved best genome for "
                    f"{game_id} with fitness "
                    f"{data.get('best_fitness', 0)}"
                )
            else:
                print(
                    f"⚠️ Failed to get genome for "
                    f"{game_id}: {response.text}"
                )
        except Exception as e:
            print(f"❌ Failed to reach Bot Service to fetch genome: {e}")

    # Elitism: Only update the base genome if we successfully retrieved a valid winner
    if best_genome_data:
        session["base_genome"] = best_genome_data

    # 3. Trigger next game or finish the loop
    if session["generations_left"] > 0:
        print(f"🧬 Generation complete."
              f"{session['g nerations_left']} remaining.")
        await _trigger_next_generation(training_session_id)
    else:
        print(f"🏆 Training Loop {training_session_id[:6]} Finished!")

        # Store the final champion in the database
        shorthand = "G" + str(uuid.uuid4())[:3].upper()
        name = f"genome_gen_{training_session_id[:6]}"

        # Failsafe: Save the best one we got, or the base if fetching failed on the final round
        genome_to_save = best_genome_data if best_genome_data else session["base_genome"]

        db.store_genome(name, shorthand, json.dumps(genome_to_save))
        genome_to_save = best_genome_data if best_genome_data else session["base_genome"]
        db.store_genome(name, shorthand, json.dumps(genome_to_save))
        del active_training_sessions[training_session_id]
