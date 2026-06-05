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
# ---------------------------------------------------------
# 1. THE ISOLATED PROCESS ENTRY POINT
# ---------------------------------------------------------


def run_bot_process(game_id: str,
                    bot_secret: str,
                    result_queue: multiprocessing.Queue):
    """
    Runs entirely inside a new, isolated memory space.
    """
    async def main():
        genome = Genome.random()
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
            # WAIT FOR HOST FIRST
            asyncio.sleep(5)
            if not host_ready_event.is_set():
                if state.get("host_connected") is True:
                    host_ready_event.set()
                else:
                    return  # ⛔ do nothing until host joins
            # Check if the game is over
            if state.get("status") == "ENDED":
                me = state.get("me", {})

                # --- FITNESS CALCULATION ---
                # Now handled entirely by the external module
                fitness_score = calculate_fitness(state)

                # Push the data back to the parent process
                result_queue.put({
                    "game_id": game_id,
                    "bot_id": me.get("id"),
                    "fitness": fitness_score,
                    "genome": bot.genome.__dict__
                })

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


@app.post("/api/spawn_bots")
async def spawn_bots(payload: SpawnBotsRequest):
    if payload.botCount <= 0 or payload.botCount > 100:
        raise HTTPException(status_code=400, detail="Invalid bot count")

    for _ in range(payload.botCount):
        # Spawn the child process
        p = multiprocessing.Process(
            target=run_bot_process,
            args=(payload.gameId, payload.botSecret, training_data_queue)
        )
        p.start()
        active_bot_processes.append(p)
        print(f"🚀 Spawned bot {p.pid} for game {payload.gameId}")

    # Return immediately while bots run in the background
    return {"status": "success", "message": f"Spawned {payload.botCount} bots"}
