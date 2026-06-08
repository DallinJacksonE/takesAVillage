from training_seeder import seed_genomes
from typing import Optional
import multiprocessing
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models.genetic.Genome import Genome
from models.genetic.GeneticBot import GeneticBot
from models.genetic.fitness import calculate_fitness
from botsocket import BotSocket
import json
# Global state to keep track of running processes
active_bot_processes = []
training_data_queue = multiprocessing.Queue()


def run_bot_process(game_id: str,
                    bot_secret: str,
                    result_queue: multiprocessing.Queue,
                    assigned_genome_dict: dict):  # NEW: Accept the assigned genome
    """
    Runs entirely inside a new, isolated memory space.
    """
    fitness_sent = False  # Flag to ensure we only send fitness once per game

    async def main():
        # NEW: Initialize the genome using the passed dictionary instead of random
        genome = Genome(**assigned_genome_dict)
        bot = GeneticBot(genome)

        host_ready_event = asyncio.Event()
        has_joined_event = asyncio.Event()

        socket = BotSocket(
            game_id=game_id,
            bot_secret=bot_secret,
            http_url=os.environ.get(
                "GAME_SERVER_HTTP_URL", "http://game-server:8000"),
            ws_url=os.environ.get("GAME_SERVER_WS_URL",
                                  "ws://game-server:8000/ws")
        )

        async def on_game_state(state):
            nonlocal fitness_sent
            # WAIT FOR HOST FIRST
            if not host_ready_event.is_set():
                if state.get("host_connected") is True:
                    host_ready_event.set()
                else:
                    return  # ⛔ do nothing until host joins

            # Check if the game is over
            me = state.get("me", {})
            if me.get("health") == "dead" and not fitness_sent:
                fitness_score = calculate_fitness(state)

                result_queue.put({
                    "game_id": game_id,
                    "Day": state.get("day"),
                    "bot_id": me.get("id"),
                    "fitness": fitness_score,
                    "genome": bot.genome.__dict__
                })

                fitness_sent = True  # Ensure we only send fitness once per game

            if state.get("status") == "ENDED":
                # Close the socket and exit
                await socket.disconnect()
                return

            # Normal gameplay logic
            if state.get("status") != "RUNNING":
                return

            if not host_ready_event.is_set():
                return

            action = bot.choose_action(state)
            if action:
                await socket.submit_action(action)

        socket.on_game_state = on_game_state

        success = await socket.connect()

        if success:
            while socket._listen_task and not socket._listen_task.done():
                await asyncio.sleep(1)

    asyncio.run(main())


async def process_training_data(queue: multiprocessing.Queue):
    """
    Constantly reads from the IPC queue and saves the bot results.
    In the future, this could push to AWS S3 or a Postgres DB.
    """
    while True:
        while not queue.empty():
            result = queue.get()

            # For now, let's append it to a local JSONL file
            with open("bot_training_data.jsonl", "a") as f:
                f.write(json.dumps(result) + "\n")

            print(f"📊 Saved training data! Bot Fitness: {result['fitness']}")

        await asyncio.sleep(2)  # Don't block the event loop


async def reap_zombies():
    """
    Periodically checks for finished processes and calls .join()
    on them to prevent zombie processes from eating up container RAM.
    """
    global active_bot_processes

    while True:
        alive_processes = []
        for p in active_bot_processes:
            if not p.is_alive():
                p.join()  # Crucial: releases OS resources
                print(f"🧹 Reaped finished bot process {p.pid}")
            else:
                alive_processes.append(p)

        active_bot_processes = alive_processes
        await asyncio.sleep(5)  # Check every 5 seconds

# ---------------------------------------------------------
# 3. FASTAPI SETUP & ENDPOINTS
# ---------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the background reaper when the container boots
    reaper_task = asyncio.create_task(reap_zombies())
    aggregator_task = asyncio.create_task(
        process_training_data(training_data_queue))
    yield
    # Graceful shutdown: terminate all child processes
    reaper_task.cancel()
    aggregator_task.cancel()
    for p in active_bot_processes:
        p.terminate()
        p.join()

app = FastAPI(lifespan=lifespan)


class SpawnBotsRequest(BaseModel):
    gameId: str
    botCount: int
    botSecret: str
    baseGenome: Optional[dict] = None


@app.post("/api/spawn_bots")
async def spawn_bots(payload: SpawnBotsRequest):
    if payload.botCount <= 0 or payload.botCount > 100:
        raise HTTPException(status_code=400, detail="Invalid bot count")

    # Generate the genomes based on the incoming base
    genomes = seed_genomes(payload.baseGenome, payload.botCount)

    for i in range(payload.botCount):
        # Pass the specific genome to the child process
        assigned_genome_dict = genomes[i].__dict__

        p = multiprocessing.Process(
            target=run_bot_process,
            args=(payload.gameId, payload.botSecret, training_data_queue,
                  assigned_genome_dict)  # Add genome to args
        )
        p.start()
        active_bot_processes.append(p)
        print(f"🚀 Spawned bot {p.pid} for game {payload.gameId}")

    return {"status": "success", "message": f"Spawned {payload.botCount} bots"}


@app.get("/api/genomes/{game_id}")
async def get_best_genome(game_id: str):
    """
    Scans the local training data for all bots in a specific game
    and returns the genome with the highest fitness score.
    """
    best_fitness = -1
    best_genome = None

    try:
        with open("bot_training_data.jsonl", "r") as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)

                if data.get("game_id") == game_id:
                    fitness = data.get("fitness", 0)
                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_genome = data.get("genome")

    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail="Training data file not found.")

    if not best_genome:
        raise HTTPException(
            status_code=404, detail="No genomes found for this game_id.")

    return {
        "game_id": game_id,
        "best_fitness": best_fitness,
        "genome": best_genome
    }
